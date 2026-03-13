from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.models.rule import ComplianceRule


class ComplianceDocument(Base):
    __tablename__ = "compliance_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    source_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    rules_extracted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    extraction_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    rules: Mapped[List["ComplianceRule"]] = relationship(
        "ComplianceRule", back_populates="document", lazy="select"
    )
