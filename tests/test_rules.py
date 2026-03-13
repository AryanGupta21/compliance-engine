from __future__ import annotations

import json
import os
import tempfile

from src.rules import Rule, RuleSet, Severity


def test_ruleset_add_and_get() -> None:
    rs = RuleSet(name="Policy", version="2.0")
    rule = Rule("R001", "Test", "A test rule", Severity.LOW, "True")
    rs.add_rule(rule)
    assert rs.get_rule("R001") is rule
    assert rs.get_rule("MISSING") is None


def test_ruleset_save_and_load() -> None:
    rs = RuleSet(name="SaveTest", version="0.1")
    rs.add_rule(Rule("R001", "My Rule", "Desc", Severity.HIGH, "entity['ok']", ["tag1"]))

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        tmp_path = f.name

    try:
        rs.save(tmp_path)
        loaded = RuleSet.load(tmp_path)
        assert loaded.name == "SaveTest"
        assert loaded.version == "0.1"
        assert len(loaded.rules) == 1
        assert loaded.rules[0].id == "R001"
        assert loaded.rules[0].tags == ["tag1"]
    finally:
        os.unlink(tmp_path)
