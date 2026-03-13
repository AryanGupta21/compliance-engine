from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .evaluator import RuleResult
from .rules import RuleSet


@dataclass
class ComplianceReport:
    """Holds the outcome of evaluating an entity against a ruleset."""

    entity: dict[str, Any]
    ruleset: RuleSet
    results: list[RuleResult]

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failed_rules(self) -> list[RuleResult]:
        return [r for r in self.results if not r.passed]

    @property
    def passed_rules(self) -> list[RuleResult]:
        return [r for r in self.results if r.passed]

    def summary(self) -> str:
        total = len(self.results)
        passed = len(self.passed_rules)
        failed = len(self.failed_rules)
        status = "COMPLIANT" if self.passed else "NON-COMPLIANT"
        lines = [
            f"=== Compliance Report: {self.ruleset.name} v{self.ruleset.version} ===",
            f"Status : {status}",
            f"Rules  : {passed}/{total} passed, {failed} failed",
        ]
        if self.failed_rules:
            lines.append("\nFailed Rules:")
            for r in self.failed_rules:
                lines.append(f"  [{r.rule.severity.upper()}] {r.rule.id} - {r.message}")
        return "\n".join(lines)
