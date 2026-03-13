"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compliance_documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("raw_text", sa.Text, nullable=False),
        sa.Column("ingested_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("rules_extracted", sa.Boolean, default=False),
        sa.Column("extraction_error", sa.Text, nullable=True),
    )
    op.create_table(
        "compliance_rules",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("document_id", sa.Integer, sa.ForeignKey("compliance_documents.id"), nullable=False),
        sa.Column("rule_title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("regex_patterns", sa.Text, nullable=False),
        sa.Column("languages", sa.Text, nullable=False),
        sa.Column("remediation", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_rules_category", "compliance_rules", ["category"])
    op.create_index("idx_rules_severity", "compliance_rules", ["severity"])
    op.create_index("idx_rules_active", "compliance_rules", ["is_active"])

    op.create_table(
        "violation_log",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("rule_id", sa.Integer, sa.ForeignKey("compliance_rules.id"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("line_number", sa.Integer, nullable=False),
        sa.Column("matched_pattern", sa.String(500), nullable=False),
        sa.Column("matched_text", sa.Text, nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("detected_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("idx_violations_rule_id", "violation_log", ["rule_id"])
    op.create_index("idx_violations_detected_at", "violation_log", ["detected_at"])


def downgrade() -> None:
    op.drop_table("violation_log")
    op.drop_index("idx_rules_active", "compliance_rules")
    op.drop_index("idx_rules_severity", "compliance_rules")
    op.drop_index("idx_rules_category", "compliance_rules")
    op.drop_table("compliance_rules")
    op.drop_table("compliance_documents")
