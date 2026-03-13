from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.document import ComplianceDocument


class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("compliance_documents.id"), nullable=False)
    rule_title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    regex_patterns: Mapped[str] = mapped_column(Text, nullable=False)   # JSON array
    languages: Mapped[str] = mapped_column(Text, nullable=False)         # JSON array
    remediation: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=True
    )

    document: Mapped["ComplianceDocument"] = relationship(
        "ComplianceDocument", back_populates="rules"
    )

    __table_args__ = (
        Index("idx_rules_category", "category"),
        Index("idx_rules_severity", "severity"),
        Index("idx_rules_active", "is_active"),
    )
