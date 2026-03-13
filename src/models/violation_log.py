from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ViolationLog(Base):
    __tablename__ = "violation_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("compliance_rules.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    matched_pattern: Mapped[str] = mapped_column(String(500), nullable=False)
    matched_text: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_violations_rule_id", "rule_id"),
        Index("idx_violations_detected_at", "detected_at"),
    )
