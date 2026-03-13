import pytest

from src.services.rule_extractor import RuleExtractor


@pytest.fixture
def extractor():
    return RuleExtractor()


def test_chunk_text_splits_correctly(extractor: RuleExtractor):
    text = "a" * 10000
    chunks = extractor._chunk_text(text, chunk_size=3000, overlap=200)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 3000


def test_chunk_text_small_doc_stays_single(extractor: RuleExtractor):
    text = "Short document."
    chunks = extractor._chunk_text(text, chunk_size=8000)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_deduplicate_removes_identical_titles(extractor: RuleExtractor):
    rules = [
        {"rule_title": "Hardcoded Password", "severity": "high"},
        {"rule_title": "Hardcoded Password", "severity": "critical"},  # duplicate
        {"rule_title": "Eval Usage", "severity": "medium"},
    ]
    unique = extractor._deduplicate_rules(rules)
    assert len(unique) == 2
    assert unique[0]["rule_title"] == "Hardcoded Password"


def test_deduplicate_normalises_title_case(extractor: RuleExtractor):
    rules = [
        {"rule_title": "Hardcoded Password"},
        {"rule_title": "hardcoded password"},
        {"rule_title": "HARDCODED PASSWORD"},
    ]
    unique = extractor._deduplicate_rules(rules)
    assert len(unique) == 1


def test_validate_rule_accepts_valid_rule(extractor: RuleExtractor):
    rule = {
        "rule_title": "Weak Crypto",
        "description": "MD5 is insecure",
        "category": "crypto",
        "severity": "high",
        "regex_patterns": [r"\bmd5\s*\("],
        "languages": ["*"],
        "remediation": "Use SHA-256 or better.",
    }
    is_valid, error = extractor._validate_rule(rule)
    assert is_valid
    assert error == ""


def test_validate_rule_rejects_invalid_severity(extractor: RuleExtractor):
    rule = {
        "rule_title": "Bad Rule",
        "description": "desc",
        "category": "general",
        "severity": "extreme",  # invalid
        "regex_patterns": [r"foo"],
        "languages": ["*"],
        "remediation": "fix it",
    }
    is_valid, _ = extractor._validate_rule(rule)
    assert not is_valid


def test_validate_rule_rejects_bad_regex(extractor: RuleExtractor):
    rule = {
        "rule_title": "Bad Regex",
        "description": "desc",
        "category": "general",
        "severity": "low",
        "regex_patterns": [r"[unclosed"],  # invalid regex
        "languages": ["*"],
        "remediation": "fix it",
    }
    is_valid, error = extractor._validate_rule(rule)
    assert not is_valid
    assert "Invalid regex" in error


def test_validate_rule_rejects_missing_fields(extractor: RuleExtractor):
    rule = {"rule_title": "Incomplete"}
    is_valid, error = extractor._validate_rule(rule)
    assert not is_valid
    assert "Missing fields" in error
