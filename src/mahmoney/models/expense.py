import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, DateTime, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from mahmoney.models.enums import Category, ExpenseStatus, PaymentMethod, Source


class Base(DeclarativeBase):
    pass


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Supplier
    supplier_name: Mapped[str] = mapped_column(String(500))
    supplier_afm: Mapped[str | None] = mapped_column(String(20), default=None)
    supplier_country: Mapped[str] = mapped_column(String(2), default="GR")

    # Invoice
    invoice_number: Mapped[str | None] = mapped_column(String(200), default=None)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Amounts
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=None)
    vat_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=None)
    vat_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=None)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="EUR")

    # Classification
    payment_method: Mapped[str] = mapped_column(String(20), default=PaymentMethod.CARD)
    category: Mapped[str] = mapped_column(String(30), default=Category.OTHER)

    # Greek tax
    mark_number: Mapped[str | None] = mapped_column(String(100), default=None)

    # Source tracking
    source: Mapped[str] = mapped_column(String(20), default=Source.MANUAL)
    source_file: Mapped[str | None] = mapped_column(String(500), default=None)
    receipt_image_path: Mapped[str | None] = mapped_column(String(500), default=None)

    # OCR
    ocr_raw_response: Mapped[dict | None] = mapped_column(JSON, default=None)
    ocr_confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), default=None)

    # Workflow
    status: Mapped[str] = mapped_column(String(20), default=ExpenseStatus.PENDING_REVIEW)
    notes: Mapped[str | None] = mapped_column(Text, default=None)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_expenses_date", "date"),
        Index("ix_expenses_status", "status"),
        Index("ix_expenses_category", "category"),
        Index("ix_expenses_supplier_afm", "supplier_afm"),
    )
