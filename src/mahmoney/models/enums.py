from enum import StrEnum


class ExpenseStatus(StrEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    EXPORTED = "exported"


class PaymentMethod(StrEnum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"


class Category(StrEnum):
    TRAVEL = "travel"
    MEALS = "meals"
    EQUIPMENT = "equipment"
    SERVICES = "services"
    SUBSCRIPTIONS = "subscriptions"
    OFFICE = "office"
    OTHER = "other"


class Source(StrEnum):
    EMAIL = "email"
    CSV_IMPORT = "csv_import"
    MANUAL = "manual"
    BREX_UPLOAD = "brex_upload"
