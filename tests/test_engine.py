from __future__ import annotations

import pytest

from src.engine import ComplianceEngine
from src.rules import Rule, RuleSet, Severity


@pytest.fixture
def simple_ruleset() -> RuleSet:
    rs = RuleSet(name="Test Policy", version="1.0")
    rs.add_rule(
        Rule(
            id="R001",
            name="Age check",
            description="Entity must be 18 or older",
            severity=Severity.HIGH,
            condition="entity['age'] >= 18",
        )
    )
    rs.add_rule(
        Rule(
            id="R002",
            name="Name required",
            description="Entity must have a non-empty name",
            severity=Severity.MEDIUM,
            condition="bool(entity.get('name', ''))",
        )
    )
    return rs


def test_compliant_entity(simple_ruleset: RuleSet) -> None:
    engine = ComplianceEngine()
    report = engine.evaluate({"age": 25, "name": "Alice"}, simple_ruleset)
    assert report.passed
    assert len(report.failed_rules) == 0


def test_non_compliant_entity(simple_ruleset: RuleSet) -> None:
    engine = ComplianceEngine()
    report = engine.evaluate({"age": 16, "name": ""}, simple_ruleset)
    assert not report.passed
    assert len(report.failed_rules) == 2


def test_batch_evaluate(simple_ruleset: RuleSet) -> None:
    engine = ComplianceEngine()
    entities = [
        {"age": 30, "name": "Bob"},
        {"age": 15, "name": ""},
    ]
    reports = engine.batch_evaluate(entities, simple_ruleset)
    assert reports[0].passed
    assert not reports[1].passed
