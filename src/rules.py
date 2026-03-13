from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Rule:
    """Represents a single compliance rule."""

    id: str
    name: str
    description: str
    severity: Severity
    condition: str  # e.g. "entity.age >= 18"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "condition": self.condition,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            severity=Severity(data["severity"]),
            condition=data["condition"],
            tags=data.get("tags", []),
        )


@dataclass
class RuleSet:
    """A named collection of compliance rules."""

    name: str
    version: str
    rules: list[Rule] = field(default_factory=list)

    def add_rule(self, rule: Rule) -> None:
        self.rules.append(rule)

    def get_rule(self, rule_id: str) -> Rule | None:
        return next((r for r in self.rules if r.id == rule_id), None)

    @classmethod
    def load(cls, path: str) -> RuleSet:
        with open(path) as f:
            data = json.load(f)
        ruleset = cls(name=data["name"], version=data["version"])
        for rule_data in data.get("rules", []):
            ruleset.add_rule(Rule.from_dict(rule_data))
        return ruleset

    def save(self, path: str) -> None:
        data = {
            "name": self.name,
            "version": self.version,
            "rules": [r.to_dict() for r in self.rules],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
