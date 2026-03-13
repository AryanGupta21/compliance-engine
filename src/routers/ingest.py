import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.document import IngestResponse
from src.services.document_parser import DocumentParser
from src.services.rule_extractor import RuleExtractor
from src.services.rule_store import RuleStore

logger = logging.getLogger(__name__)
router = APIRouter(tags=["ingest"])

_parser = DocumentParser()
_extractor = RuleExtractor()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    """Upload a regulatory document (PDF or Markdown) and extract compliance rules via AI."""
    content = await file.read()
    file_hash = DocumentParser.compute_hash(content)

    existing = await RuleStore.get_document_by_hash(db, file_hash)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Document already ingested as document_id={existing.id}. "
                   "Use GET /rules to view its extracted rules.",
        )

    try:
        file_type, raw_text = _parser.parse(file.filename or "upload", content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="Document appears to be empty or unreadable.")

    doc = await RuleStore.create_document(db, file.filename or "upload", file_type, file_hash, raw_text)

    try:
        rules_data = await _extractor.extract_from_text(raw_text, file.filename or "upload")
        rules = await RuleStore.bulk_create_rules(db, doc.id, rules_data)
        await RuleStore.mark_document_extracted(db, doc.id, success=True)
        return IngestResponse(
            document_id=doc.id,
            filename=doc.filename,
            rules_extracted=len(rules),
            message=f"Successfully extracted {len(rules)} compliance rule(s).",
        )
    except Exception as e:
        logger.exception("Rule extraction failed for document %d", doc.id)
        await RuleStore.mark_document_extracted(db, doc.id, success=False, error=str(e))
        raise HTTPException(status_code=500, detail=f"Rule extraction failed: {e}")
