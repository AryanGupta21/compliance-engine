import logging
import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.violation_log import ViolationLog
from src.schemas.precommit import FileChange, Finding
from src.services.rule_store import RuleStore
from src.utils.language_detector import detect_language
from src.utils.regex_utils import compile_pattern

logger = logging.getLogger(__name__)


@dataclass
class MatchContext:
    rule_id: int
    rule_title: str
    severity: str
    pattern: str
    remediation: str
    line_number: int
    matched_text: str


class ValidationEngine:

    def _rule_applies(self, rule: dict, language: str) -> bool:
        langs = rule["languages"]
        return "*" in langs or language in langs

    def _scan_file(self, file: FileChange, rules: list[dict]) -> list[MatchContext]:
        """
        Scan a single file line-by-line against all applicable rules.
        Returns one MatchContext per (rule, pattern, line) combination.
        Breaking after first match per pattern per line prevents duplicate findings.
        """
        language = detect_language(file.file_path)
        lines = file.content.splitlines()
        matches: list[MatchContext] = []

        for rule in rules:
            if not self._rule_applies(rule, language):
                continue

            for pattern_str in rule["regex_patterns"]:
                try:
                    compiled = compile_pattern(pattern_str)
                except re.error:
                    logger.warning("Skipping invalid pattern in rule %d: %s", rule["id"], pattern_str)
                    continue

                for line_num, line in enumerate(lines, start=1):
                    if compiled.search(line):
                        matches.append(
                            MatchContext(
                                rule_id=rule["id"],
                                rule_title=rule["rule_title"],
                                severity=rule["severity"],
                                pattern=pattern_str,
                                remediation=rule["remediation"],
                                line_number=line_num,
                                matched_text=line.strip()[:200],
                            )
                        )
                        break  # one match per pattern per file is enough

        return matches

    async def validate(self, files: list[FileChange], db: AsyncSession) -> list[Finding]:
        """
        Full validation pipeline:
        1. Load active rules from DB
        2. Scan each file
        3. Audit-log all violations
        4. Return Finding list
        """
        rules = await RuleStore.list_rules(db, active_only=True)
        all_findings: list[Finding] = []
        violation_logs: list[ViolationLog] = []

        for file in files:
            language = detect_language(file.file_path)
            matches = self._scan_file(file, rules)

            for ctx in matches:
                all_findings.append(
                    Finding(
                        rule_id=str(ctx.rule_id),
                        severity=ctx.severity,
                        line_number=ctx.line_number,
                        message=f"[{ctx.rule_title}] {ctx.matched_text[:100]}",
                        remediation=ctx.remediation,
                    )
                )
                violation_logs.append(
                    ViolationLog(
                        rule_id=ctx.rule_id,
                        file_path=file.file_path,
                        language=language,
                        line_number=ctx.line_number,
                        matched_pattern=ctx.pattern,
                        matched_text=ctx.matched_text,
                        severity=ctx.severity,
                    )
                )

        if violation_logs:
            db.add_all(violation_logs)
            await db.commit()

        return all_findings
