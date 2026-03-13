from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .evaluator import Evaluator
from .report import ComplianceReport
from .rules import RuleSet


@dataclass
class ComplianceEngine:
    """Core compliance engine that orchestrates rule evaluation."""

    evaluator: Evaluator = field(default_factory=Evaluator)

    def evaluate(self, entity: dict[str, Any], ruleset: RuleSet) -> ComplianceReport:
        """Evaluate an entity against a ruleset and return a compliance report."""
        results = self.evaluator.run(entity, ruleset)
        return ComplianceReport(entity=entity, ruleset=ruleset, results=results)

    def batch_evaluate(
        self, entities: list[dict[str, Any]], ruleset: RuleSet
    ) -> list[ComplianceReport]:
        """Evaluate multiple entities against the same ruleset."""
        return [self.evaluate(entity, ruleset) for entity in entities]
