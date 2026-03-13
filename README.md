# Compliance Engine

A rule-based compliance engine for evaluating policies and regulatory requirements.

## Features

- Define and manage compliance rules
- Evaluate entities against rule sets
- Generate compliance reports
- Support for multiple policy frameworks

## Project Structure

```
compliance-engine/
├── src/
│   ├── engine.py        # Core compliance engine
│   ├── rules.py         # Rule definitions and parser
│   ├── evaluator.py     # Rule evaluator
│   └── report.py        # Report generation
├── tests/
│   ├── test_engine.py
│   ├── test_rules.py
│   └── test_evaluator.py
├── requirements.txt
└── README.md
```

## Getting Started

```bash
pip install -r requirements.txt
python -m src.engine
```

## Usage

```python
from src.engine import ComplianceEngine
from src.rules import Rule, RuleSet

engine = ComplianceEngine()
ruleset = RuleSet.load("policies/gdpr.json")
result = engine.evaluate(entity={"name": "Acme Corp"}, ruleset=ruleset)
print(result.summary())
```

## License

MIT
