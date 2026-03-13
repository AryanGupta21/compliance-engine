from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.document import DocumentResponse
from src.services.rule_store import RuleStore

router = APIRouter(tags=["documents"])


@router.get("/documents", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)) -> list[DocumentResponse]:
    """List all ingested regulatory documents with their rule counts."""
    docs = await RuleStore.list_documents(db)
    return [DocumentResponse(**d) for d in docs]
