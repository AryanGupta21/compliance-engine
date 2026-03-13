from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


SAMPLE_RULE = {
    "rule_title": "Eval Usage",
    "description": "Direct use of eval() is dangerous",
    "category": "injection",
    "severity": "high",
    "regex_patterns": [r"\beval\s*\("],
    "languages": ["python", "javascript"],
    "remediation": "Avoid eval(). Use safer alternatives.",
}

SAMPLE_MD = b"# Security Policy\n\nDo not use eval() in code. Hardcoded secrets are forbidden."


@pytest.mark.asyncio
async def test_ingest_markdown_returns_rules(client: AsyncClient, db: AsyncSession):
    with patch(
        "src.routers.ingest._extractor.extract_from_text",
        new=AsyncMock(return_value=[SAMPLE_RULE]),
    ):
        response = await client.post(
            "/ingest",
            files={"file": ("security_policy.md", SAMPLE_MD, "text/markdown")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["rules_extracted"] == 1
    assert data["filename"] == "security_policy.md"
    assert "document_id" in data


@pytest.mark.asyncio
async def test_ingest_duplicate_returns_409(client: AsyncClient, db: AsyncSession):
    with patch(
        "src.routers.ingest._extractor.extract_from_text",
        new=AsyncMock(return_value=[SAMPLE_RULE]),
    ):
        await client.post(
            "/ingest",
            files={"file": ("policy.md", SAMPLE_MD, "text/markdown")},
        )
        response = await client.post(
            "/ingest",
            files={"file": ("policy.md", SAMPLE_MD, "text/markdown")},
        )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_ingest_unsupported_type_returns_400(client: AsyncClient, db: AsyncSession):
    response = await client.post(
        "/ingest",
        files={"file": ("policy.docx", b"data", "application/octet-stream")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_ingest_zero_rules_still_succeeds(client: AsyncClient, db: AsyncSession):
    with patch(
        "src.routers.ingest._extractor.extract_from_text",
        new=AsyncMock(return_value=[]),
    ):
        response = await client.post(
            "/ingest",
            files={"file": ("empty_policy.md", b"# Nothing here", "text/markdown")},
        )
    assert response.status_code == 200
    assert response.json()["rules_extracted"] == 0
