from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .rules import Rule, RuleSet, Severity


@dataclass
class RuleResult:
    rule: Rule
    passed: bool
    message: str = ""


class Evaluator:
    """Evaluates entities against compliance rules."""

    def run(self, entity: dict[str, Any], ruleset: RuleSet) -> list[RuleResult]:
        results: list[RuleResult] = []
        for rule in ruleset.rules:
            result = self._evaluate_rule(entity, rule)
            results.append(result)
        return results

    def _evaluate_rule(self, entity: dict[str, Any], rule: Rule) -> RuleResult:
        try:
            passed = bool(eval(rule.condition, {"entity": entity}))  # noqa: S307
            message = "PASS" if passed else f"FAIL: {rule.description}"
        except Exception as exc:
            passed = False
            message = f"ERROR evaluating rule '{rule.id}': {exc}"
        return RuleResult(rule=rule, passed=passed, message=message)

    def critical_failures(self, results: list[RuleResult]) -> list[RuleResult]:
        return [
            r
            for r in results
            if not r.passed and r.rule.severity == Severity.CRITICAL
        ]
