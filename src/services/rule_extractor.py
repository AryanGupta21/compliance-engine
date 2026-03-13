import logging
import re

from src.ai.gemini_client import GeminiClient
from src.config import settings

logger = logging.getLogger(__name__)

VALID_SEVERITIES = {"critical", "high", "medium", "low"}
VALID_CATEGORIES = {
    "secrets", "pii", "crypto", "auth", "logging",
    "injection", "configuration", "dependency", "network", "general",
}


class RuleExtractor:
    def __init__(self) -> None:
        self.gemini = GeminiClient()

    def _chunk_text(self, text: str, chunk_size: int, overlap: int = 500) -> list[str]:
        """
        Split text into overlapping chunks, preferring paragraph boundaries.
        Overlap prevents rules that straddle chunk edges from being missed.
        """
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                boundary = text.rfind("\n\n", start, end)
                if boundary > start + chunk_size // 2:
                    end = boundary
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = end - overlap  # overlap prevents boundary misses
        return chunks

    def _deduplicate_rules(self, rules: list[dict]) -> list[dict]:
        """Remove rules with duplicate titles (normalised to alphanumeric lowercase)."""
        seen: set[str] = set()
        unique: list[dict] = []
        for rule in rules:
            key = re.sub(r"\W+", "", rule.get("rule_title", "")).lower()
            if key and key not in seen:
                seen.add(key)
                unique.append(rule)
        return unique

    def _validate_rule(self, rule: dict) -> tuple[bool, str]:
        """Return (is_valid, error_message). Checks required fields and regex compilability."""
        required = {"rule_title", "description", "category", "severity", "regex_patterns", "languages", "remediation"}
        missing = required - set(rule.keys())
        if missing:
            return False, f"Missing fields: {missing}"

        if rule["severity"] not in VALID_SEVERITIES:
            return False, f"Invalid severity '{rule['severity']}'"

        if not isinstance(rule.get("regex_patterns"), list) or not rule["regex_patterns"]:
            return False, "regex_patterns must be a non-empty list"

        for pattern in rule["regex_patterns"]:
            try:
                re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                return False, f"Invalid regex '{pattern}': {e}"

        return True, ""

    async def extract_from_text(self, text: str, document_name: str) -> list[dict]:
        """
        Chunk text, send each chunk to Claude, deduplicate and validate the results.
        Returns a list of valid rule dicts ready for DB insertion.
        """
        chunks = self._chunk_text(text, settings.MAX_CHUNK_SIZE)
        all_rules: list[dict] = []

        for i, chunk in enumerate(chunks):
            try:
                chunk_rules = await self.gemini.extract_rules(
                    text_chunk=chunk,
                    document_name=document_name,
                    chunk_index=i + 1,
                    total_chunks=len(chunks),
                )
                all_rules.extend(chunk_rules)
            except Exception as e:
                logger.error("Failed to process chunk %d/%d: %s", i + 1, len(chunks), e)

        unique = self._deduplicate_rules(all_rules)
        unique = unique[: settings.MAX_RULES_PER_DOCUMENT]

        valid_rules: list[dict] = []
        for rule in unique:
            is_valid, error = self._validate_rule(rule)
            if is_valid:
                valid_rules.append(rule)
            else:
                logger.warning("Skipping invalid rule '%s': %s", rule.get("rule_title"), error)

        return valid_rules
