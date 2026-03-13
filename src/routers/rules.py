from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.schemas.rule import RuleResponse, RuleUpdate
from src.services.rule_store import RuleStore

router = APIRouter(tags=["rules"])


@router.get("/rules", response_model=list[RuleResponse])
async def list_rules(
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    language: Optional[str] = Query(None, description="Filter by target language"),
    db: AsyncSession = Depends(get_db),
) -> list[RuleResponse]:
    """List active compliance rules with optional filters."""
    rules = await RuleStore.list_rules(db, category=category, severity=severity, language=language)
    return [RuleResponse(**r) for r in rules]


@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: int, db: AsyncSession = Depends(get_db)) -> RuleResponse:
    """Retrieve a single compliance rule by ID."""
    rule = await RuleStore.get_rule(db, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found.")
    return RuleResponse(**rule)


@router.put("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    update: RuleUpdate,
    db: AsyncSession = Depends(get_db),
) -> RuleResponse:
    """Partially update a compliance rule (e.g. edit patterns, change severity, deactivate)."""
    rule = await RuleStore.update_rule(db, rule_id, update)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found.")
    return RuleResponse(**rule)


@router.delete("/rules/{rule_id}", status_code=204)
async def deactivate_rule(rule_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Soft-delete a rule (sets is_active=False). It will no longer trigger violations."""
    success = await RuleStore.deactivate_rule(db, rule_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found.")
