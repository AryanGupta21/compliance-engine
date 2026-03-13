import json
import logging

import anthropic

from src.ai.prompts import JSON_REPAIR_PROMPT, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.config import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def extract_rules(
        self,
        text_chunk: str,
        document_name: str,
        chunk_index: int,
        total_chunks: int,
    ) -> list[dict]:
        """Send a single text chunk to Claude and return a list of parsed rule dicts."""
        user_content = USER_PROMPT_TEMPLATE.format(
            document_name=document_name,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            text_chunk=text_chunk,
        )
        message = await self._client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = message.content[0].text.strip()

        # Strip markdown fencing if Claude added it despite instructions
        if raw.startswith("```"):
            raw = raw.split("```", 2)[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rsplit("```", 1)[0].strip()

        try:
            result = json.loads(raw)
            if not isinstance(result, list):
                logger.warning("Claude returned non-list JSON, wrapping in list")
                result = [result] if isinstance(result, dict) else []
            return result
        except json.JSONDecodeError as e:
            logger.warning("JSON parse failed for chunk %d/%d, attempting repair: %s", chunk_index, total_chunks, e)
            return await self._repair_json(raw, str(e))

    async def _repair_json(self, broken: str, error: str) -> list[dict]:
        """Follow-up call asking Claude to fix its own malformed JSON output."""
        message = await self._client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=4096,
            system="You are a JSON repair assistant. Return ONLY valid JSON, nothing else.",
            messages=[{
                "role": "user",
                "content": JSON_REPAIR_PROMPT.format(error=error, broken=broken),
            }],
        )
        raw = message.content[0].text.strip()
        try:
            result = json.loads(raw)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError:
            logger.error("JSON repair also failed, returning empty list")
            return []
