"""Initial schema: expenses table

Revision ID: 001
Revises:
Create Date: 2026-03-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("supplier_name", sa.String(500), nullable=False),
        sa.Column("supplier_afm", sa.String(20), nullable=True),
        sa.Column("supplier_country", sa.String(2), nullable=False, server_default="GR"),
        sa.Column("invoice_number", sa.String(200), nullable=True),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("net_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("vat_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("vat_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="EUR"),
        sa.Column("payment_method", sa.String(20), nullable=False, server_default="card"),
        sa.Column("category", sa.String(30), nullable=False, server_default="other"),
        sa.Column("mark_number", sa.String(100), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("source_file", sa.String(500), nullable=True),
        sa.Column("receipt_image_path", sa.String(500), nullable=True),
        sa.Column("ocr_raw_response", JSONB, nullable=True),
        sa.Column("ocr_confidence", sa.Numeric(3, 2), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending_review"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index("ix_expenses_date", "expenses", ["date"])
    op.create_index("ix_expenses_status", "expenses", ["status"])
    op.create_index("ix_expenses_category", "expenses", ["category"])
    op.create_index("ix_expenses_supplier_afm", "expenses", ["supplier_afm"])


def downgrade() -> None:
    op.drop_index("ix_expenses_supplier_afm")
    op.drop_index("ix_expenses_category")
    op.drop_index("ix_expenses_status")
    op.drop_index("ix_expenses_date")
    op.drop_table("expenses")
