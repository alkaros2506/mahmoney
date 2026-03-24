import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from mahmoney.models.enums import Category, ExpenseStatus, PaymentMethod, Source


class ExpenseCreate(BaseModel):
    supplier_name: str
    supplier_afm: str | None = None
    supplier_country: str = "GR"
    invoice_number: str | None = None
    date: datetime
    net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    vat_rate: Decimal | None = None
    total_amount: Decimal
    currency: str = "EUR"
    payment_method: PaymentMethod = PaymentMethod.CARD
    category: Category = Category.OTHER
    mark_number: str | None = None
    source: Source = Source.MANUAL
    source_file: str | None = None
    notes: str | None = None


class ExpenseUpdate(BaseModel):
    supplier_name: str | None = None
    supplier_afm: str | None = None
    supplier_country: str | None = None
    invoice_number: str | None = None
    date: datetime | None = None
    net_amount: Decimal | None = None
    vat_amount: Decimal | None = None
    vat_rate: Decimal | None = None
    total_amount: Decimal | None = None
    currency: str | None = None
    payment_method: PaymentMethod | None = None
    category: Category | None = None
    mark_number: str | None = None
    status: ExpenseStatus | None = None
    notes: str | None = None


class ExpenseResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    supplier_name: str
    supplier_afm: str | None
    supplier_country: str
    invoice_number: str | None
    date: datetime
    net_amount: Decimal | None
    vat_amount: Decimal | None
    vat_rate: Decimal | None
    total_amount: Decimal
    currency: str
    payment_method: str
    category: str
    mark_number: str | None
    source: str
    source_file: str | None
    receipt_image_path: str | None
    ocr_confidence: Decimal | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int
    page: int
    per_page: int


class DashboardSummary(BaseModel):
    total_expenses: int
    total_amount_eur: Decimal
    by_category: dict[str, Decimal]
    by_month: dict[str, Decimal]
    by_status: dict[str, int]
    pending_review_count: int


class BulkImportResponse(BaseModel):
    imported: int
    errors: list[str] = Field(default_factory=list)
