from mahmoney.models.enums import Category, ExpenseStatus, PaymentMethod, Source


def test_expense_status_values():
    assert ExpenseStatus.PENDING_REVIEW == "pending_review"
    assert ExpenseStatus.APPROVED == "approved"
    assert ExpenseStatus.EXPORTED == "exported"


def test_payment_method_values():
    assert PaymentMethod.CASH == "cash"
    assert PaymentMethod.CARD == "card"
    assert PaymentMethod.BANK_TRANSFER == "bank_transfer"


def test_category_values():
    assert Category.TRAVEL == "travel"
    assert Category.MEALS == "meals"
    assert Category.EQUIPMENT == "equipment"
    assert Category.SERVICES == "services"
    assert Category.SUBSCRIPTIONS == "subscriptions"
    assert Category.OFFICE == "office"
    assert Category.OTHER == "other"


def test_source_values():
    assert Source.EMAIL == "email"
    assert Source.CSV_IMPORT == "csv_import"
    assert Source.MANUAL == "manual"
    assert Source.BREX_UPLOAD == "brex_upload"
