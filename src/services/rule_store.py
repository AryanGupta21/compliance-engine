import json
import logging
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.document import ComplianceDocument
from src.models.rule import ComplianceRule
from src.schemas.rule import RuleUpdate

logger = logging.getLogger(__name__)


class RuleStore:

    # ------------------------------------------------------------------ #
    # Documents                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def get_document_by_hash(db: AsyncSession, source_hash: str) -> Optional[ComplianceDocument]:
        result = await db.execute(
            select(ComplianceDocument).where(ComplianceDocument.source_hash == source_hash)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_document(
        db: AsyncSession,
        filename: str,
        file_type: str,
        source_hash: str,
        raw_text: str,
    ) -> ComplianceDocument:
        doc = ComplianceDocument(
            filename=filename,
            file_type=file_type,
            source_hash=source_hash,
            raw_text=raw_text,
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def mark_document_extracted(
        db: AsyncSession,
        document_id: int,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        result = await db.execute(
            select(ComplianceDocument).where(ComplianceDocument.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc:
            doc.rules_extracted = success
            doc.extraction_error = error
            await db.commit()

    @staticmethod
    async def list_documents(db: AsyncSession) -> list[dict]:
        result = await db.execute(
            select(
                ComplianceDocument,
                func.count(ComplianceRule.id).label("rule_count"),
            )
            .outerjoin(ComplianceRule, ComplianceRule.document_id == ComplianceDocument.id)
            .group_by(ComplianceDocument.id)
            .order_by(ComplianceDocument.ingested_at.desc())
        )
        rows = result.all()
        docs = []
        for doc, rule_count in rows:
            d = {
                "id": doc.id,
                "filename": doc.filename,
                "file_type": doc.file_type,
                "source_hash": doc.source_hash,
                "ingested_at": doc.ingested_at,
                "rules_extracted": doc.rules_extracted,
                "extraction_error": doc.extraction_error,
                "rule_count": rule_count,
            }
            docs.append(d)
        return docs

    # ------------------------------------------------------------------ #
    # Rules                                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def bulk_create_rules(
        db: AsyncSession, document_id: int, rules_data: list[dict]
    ) -> list[ComplianceRule]:
        rules = [
            ComplianceRule(
                document_id=document_id,
                rule_title=r["rule_title"],
                description=r["description"],
                category=r.get("category", "general"),
                severity=r["severity"],
                regex_patterns=json.dumps(r["regex_patterns"]),
                languages=json.dumps(r.get("languages", ["*"])),
                remediation=r["remediation"],
            )
            for r in rules_data
        ]
        db.add_all(rules)
        await db.commit()
        for rule in rules:
            await db.refresh(rule)
        return rules

    @staticmethod
    async def list_rules(
        db: AsyncSession,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        language: Optional[str] = None,
        active_only: bool = True,
    ) -> list[dict]:
        query = select(ComplianceRule)
        if active_only:
            query = query.where(ComplianceRule.is_active == True)  # noqa: E712
        if category:
            query = query.where(ComplianceRule.category == category)
        if severity:
            query = query.where(ComplianceRule.severity == severity)
        query = query.order_by(ComplianceRule.id)

        result = await db.execute(query)
        rules = result.scalars().all()

        rule_dicts = []
        for r in rules:
            langs = json.loads(r.languages)
            if language and "*" not in langs and language not in langs:
                continue
            rule_dicts.append(_rule_to_dict(r))
        return rule_dicts

    @staticmethod
    async def get_rule(db: AsyncSession, rule_id: int) -> Optional[dict]:
        result = await db.execute(
            select(ComplianceRule).where(ComplianceRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        return _rule_to_dict(rule) if rule else None

    @staticmethod
    async def update_rule(
        db: AsyncSession, rule_id: int, update: RuleUpdate
    ) -> Optional[dict]:
        result = await db.execute(
            select(ComplianceRule).where(ComplianceRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if not rule:
            return None

        data = update.model_dump(exclude_unset=True)
        for field, value in data.items():
            if field == "regex_patterns":
                setattr(rule, field, json.dumps(value))
            elif field == "languages":
                setattr(rule, field, json.dumps(value))
            else:
                setattr(rule, field, value)

        await db.commit()
        await db.refresh(rule)
        return _rule_to_dict(rule)

    @staticmethod
    async def deactivate_rule(db: AsyncSession, rule_id: int) -> bool:
        result = await db.execute(
            select(ComplianceRule).where(ComplianceRule.id == rule_id)
        )
        rule = result.scalar_one_or_none()
        if not rule:
            return False
        rule.is_active = False
        await db.commit()
        return True


def _rule_to_dict(rule: ComplianceRule) -> dict:
    return {
        "id": rule.id,
        "document_id": rule.document_id,
        "rule_title": rule.rule_title,
        "description": rule.description,
        "category": rule.category,
        "severity": rule.severity,
        "regex_patterns": json.loads(rule.regex_patterns),
        "languages": json.loads(rule.languages),
        "remediation": rule.remediation,
        "is_active": rule.is_active,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }
