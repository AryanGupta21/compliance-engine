from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.precommit import ValidateRequest, ValidateResponse
from src.services.validator import ValidationEngine

router = APIRouter(tags=["validation"])
_engine = ValidationEngine()


@router.post("/validate", response_model=ValidateResponse)
async def validate_files(
    request: ValidateRequest,
    db: AsyncSession = Depends(get_db),
) -> ValidateResponse:
    """
    Main integration endpoint for the Pre-Commit Engine (SecretLens).
    Receives a list of FileChange objects, scans them against stored compliance rules,
    and returns a list of Findings.
    """
    findings = await _engine.validate(request.files, db)
    return ValidateResponse(findings=findings)
