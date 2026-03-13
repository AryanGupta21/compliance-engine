# Compliance Engine

A regulatory compliance engine that extracts enforceable rules from policy documents (PDF/Markdown)
using the Claude AI API and validates source code files against them. Designed to integrate with the
Pre-Commit Engine (SecretLens).

## Architecture

```
compliance-engine/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings (pydantic-settings / .env)
│   ├── database.py          # Async SQLAlchemy + SQLite
│   ├── models/              # ORM models (documents, rules, violations)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── routers/             # FastAPI route handlers
│   ├── services/            # Business logic (parsing, extraction, validation)
│   ├── ai/                  # Claude API client + prompts
│   └── utils/               # Language detection, regex caching
└── tests/                   # pytest-asyncio test suite
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Service health check |
| POST | /ingest | Upload PDF or Markdown → AI rule extraction |
| GET | /documents | List all ingested documents |
| GET | /rules | List active rules (filters: category, severity, language) |
| GET | /rules/{id} | Get a single rule |
| PUT | /rules/{id} | Update / override a rule |
| DELETE | /rules/{id} | Soft-delete a rule |
| POST | /validate | **SecretLens integration** — validate code files, return violations |

## Getting Started

### 1. Set up environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and set your ANTHROPIC_API_KEY
```

### 3. Run the server

```bash
uvicorn src.main:app --reload --port 8000
```

The database is created automatically at `data/compliance.db` on first start.

### 4. Ingest a compliance document

```bash
curl -X POST http://localhost:8000/ingest \
     -F "file=@your_policy.pdf"
```

### 5. View extracted rules

```bash
curl http://localhost:8000/rules | python3 -m json.tool
```

### 6. Validate code (simulate Pre-Commit Engine)

```bash
curl -X POST http://localhost:8000/validate \
     -H "Content-Type: application/json" \
     -d '{
       "files": [
         {
           "file_path": "app/config.py",
           "content": "DB_PASSWORD = \"supersecret123\"\nAPI_KEY = \"sk-prod-abc\""
         }
       ],
       "ai_provider_config": {}
     }'
```

### 7. Interactive API docs

```
open http://localhost:8000/docs
```

## Running Tests

```bash
pytest tests/ -v
```

Tests use an in-memory SQLite database and mock the Claude API — no API key required.

## Pre-Commit Engine Integration

The `/validate` endpoint accepts the same `FileChange` format that SecretLens uses:

```json
{
  "files": [{"file_path": "...", "content": "..."}],
  "ai_provider_config": {}
}
```

And returns `Finding` objects compatible with the SecretLens response format:

```json
{
  "findings": [
    {
      "rule_id": "1",
      "severity": "critical",
      "line_number": 3,
      "message": "[Rule Title] matched text...",
      "remediation": "Guidance text"
    }
  ]
}
```

## License

MIT
