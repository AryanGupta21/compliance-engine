import json

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import ComplianceDocument
from src.models.rule import ComplianceRule


async def _seed_rule(db: AsyncSession, **kwargs) -> ComplianceRule:
    """Helper: insert a document + rule directly into the test DB."""
    doc = ComplianceDocument(
        filename="test_policy.md",
        file_type="markdown",
        source_hash=kwargs.get("doc_hash", "abc123"),
        raw_text="test policy",
        rules_extracted=True,
    )
    db.add(doc)
    await db.flush()

    rule = ComplianceRule(
        document_id=doc.id,
        rule_title=kwargs.get("rule_title", "Hardcoded Password"),
        description=kwargs.get("description", "Detects hardcoded passwords"),
        category=kwargs.get("category", "secrets"),
        severity=kwargs.get("severity", "critical"),
        regex_patterns=json.dumps(kwargs.get("patterns", [r"password\s*=\s*[\"'][^\"']{4,}[\"']"])),
        languages=json.dumps(kwargs.get("languages", ["*"])),
        remediation=kwargs.get("remediation", "Use environment variables."),
        is_active=kwargs.get("is_active", True),
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@pytest.mark.asyncio
async def test_validate_no_rules_returns_empty(client: AsyncClient, db: AsyncSession):
    response = await client.post(
        "/validate",
        json={"files": [{"file_path": "app.py", "content": 'password = "secret123"'}], "ai_provider_config": {}},
    )
    assert response.status_code == 200
    assert response.json()["findings"] == []


@pytest.mark.asyncio
async def test_validate_detects_violation(client: AsyncClient, db: AsyncSession):
    await _seed_rule(db)
    response = await client.post(
        "/validate",
        json={"files": [{"file_path": "config.py", "content": 'db_password = "supersecret"'}], "ai_provider_config": {}},
    )
    assert response.status_code == 200
    findings = response.json()["findings"]
    assert len(findings) == 1
    assert findings[0]["severity"] == "critical"
    assert findings[0]["line_number"] == 1


@pytest.mark.asyncio
async def test_validate_finding_has_correct_wire_format(client: AsyncClient, db: AsyncSession):
    rule = await _seed_rule(db)
    response = await client.post(
        "/validate",
        json={"files": [{"file_path": "app.py", "content": 'x_password = "abc12345"'}], "ai_provider_config": {}},
    )
    findings = response.json()["findings"]
    assert len(findings) == 1
    f = findings[0]
    assert f["rule_id"] == str(rule.id)
    assert f["severity"] in {"critical", "high", "medium", "low"}
    assert isinstance(f["line_number"], int)
    assert "message" in f
    assert "remediation" in f


@pytest.mark.asyncio
async def test_validate_language_filter_skips_wrong_language(client: AsyncClient, db: AsyncSession):
    """A Python-only rule should NOT trigger on a .js file."""
    await _seed_rule(db, doc_hash="py_hash", languages=["python"], patterns=[r"password\s*=\s*[\"'][^\"']+[\"']"])
    response = await client.post(
        "/validate",
        json={"files": [{"file_path": "app.js", "content": 'const password = "hunter2"'}], "ai_provider_config": {}},
    )
    assert response.json()["findings"] == []


@pytest.mark.asyncio
async def test_validate_universal_rule_triggers_on_any_language(client: AsyncClient, db: AsyncSession):
    """A rule with languages=["*"] should trigger on any file."""
    await _seed_rule(db, doc_hash="any_hash", languages=["*"], patterns=[r"eval\s*\("])
    response = await client.post(
        "/validate",
        json={"files": [{"file_path": "script.rb", "content": "eval(user_input)"}], "ai_provider_config": {}},
    )
    assert len(response.json()["findings"]) == 1


@pytest.mark.asyncio
async def test_validate_inactive_rule_is_ignored(client: AsyncClient, db: AsyncSession):
    await _seed_rule(db, doc_hash="inactive_hash", is_active=False)
    response = await client.post(
        "/validate",
        json={"files": [{"file_path": "app.py", "content": 'password = "secret99"'}], "ai_provider_config": {}},
    )
    assert response.json()["findings"] == []


@pytest.mark.asyncio
async def test_validate_multiline_file(client: AsyncClient, db: AsyncSession):
    await _seed_rule(db)
    code = "\n".join([
        "import os",
        "host = 'localhost'",
        'db_password = "mysecret1"',
        "port = 5432",
    ])
    response = await client.post(
        "/validate",
        json={"files": [{"file_path": "settings.py", "content": code}], "ai_provider_config": {}},
    )
    findings = response.json()["findings"]
    assert len(findings) == 1
    assert findings[0]["line_number"] == 3


@pytest.mark.asyncio
async def test_validate_multiple_files(client: AsyncClient, db: AsyncSession):
    await _seed_rule(db)
    response = await client.post(
        "/validate",
        json={
            "files": [
                {"file_path": "a.py", "content": 'password = "pw12345"'},
                {"file_path": "b.py", "content": "x = 1  # clean"},
                {"file_path": "c.py", "content": 'secret_password = "abc99999"'},
            ],
            "ai_provider_config": {},
        },
    )
    findings = response.json()["findings"]
    assert len(findings) == 2
