from __future__ import annotations

from src.evaluator import Evaluator
from src.rules import Rule, RuleSet, Severity


def test_evaluator_pass() -> None:
    evaluator = Evaluator()
    rule = Rule(
        id="R001",
        name="Positive balance",
        description="Balance must be non-negative",
        severity=Severity.CRITICAL,
        condition="entity['balance'] >= 0",
    )
    rs = RuleSet(name="Finance", version="1.0", rules=[rule])
    results = evaluator.run({"balance": 100}, rs)
    assert results[0].passed


def test_evaluator_fail() -> None:
    evaluator = Evaluator()
    rule = Rule(
        id="R001",
        name="Positive balance",
        description="Balance must be non-negative",
        severity=Severity.CRITICAL,
        condition="entity['balance'] >= 0",
    )
    rs = RuleSet(name="Finance", version="1.0", rules=[rule])
    results = evaluator.run({"balance": -50}, rs)
    assert not results[0].passed


def test_critical_failures() -> None:
    evaluator = Evaluator()
    rules = [
        Rule("R001", "Critical rule", "Must pass", Severity.CRITICAL, "entity['x'] > 0"),
        Rule("R002", "Low rule", "Low priority", Severity.LOW, "entity['y'] > 0"),
    ]
    rs = RuleSet(name="Mixed", version="1.0", rules=rules)
    results = evaluator.run({"x": -1, "y": -1}, rs)
    critical = evaluator.critical_failures(results)
    assert len(critical) == 1
    assert critical[0].rule.id == "R001"
