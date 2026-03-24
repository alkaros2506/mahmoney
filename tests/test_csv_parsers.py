from mahmoney.parsers.chase import ChaseParser
from mahmoney.parsers.eurobank import EurobankParser
from mahmoney.parsers.revolut import RevolutParser
from mahmoney.services.csv_parser import detect_format

EUROBANK_CSV = """Ημερομηνία,Περιγραφή,Ποσό,Υπόλοιπο
15/01/2026,COSMOTE ΠΛΗΡΩΜΗ,-45.00,1000.00
16/01/2026,ΣΚΛΑΒΕΝΙΤΗΣ,-82.30,917.70
17/01/2026,ΜΙΣΘΟΣ,2500.00,3417.70
"""

CHASE_CSV = """Transaction Date,Post Date,Description,Category,Type,Amount,Memo
01/15/2026,01/16/2026,UBER TRIP,Travel,Sale,-25.43,
01/16/2026,01/17/2026,AMAZON.COM,Shopping,Sale,-199.99,
01/17/2026,01/18/2026,PAYMENT RECEIVED,,Payment,500.00,
"""

REVOLUT_CSV = """Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance
CARD_PAYMENT,Current,2026-01-15 10:30:00,2026-01-15 10:30:00,Bolt Ride,-8.50,0.00,EUR,COMPLETED,500.00
CARD_PAYMENT,Current,2026-01-16 12:00:00,2026-01-16 12:00:00,Wolt Delivery,-22.40,0.00,EUR,COMPLETED,477.60
TOPUP,Current,2026-01-17 09:00:00,2026-01-17 09:00:00,Top-Up,200.00,0.00,EUR,COMPLETED,677.60
"""


def test_detect_eurobank():
    assert detect_format(EUROBANK_CSV, "statement.csv") == "eurobank"


def test_detect_chase():
    assert detect_format(CHASE_CSV, "chase_activity.csv") == "chase"


def test_detect_revolut():
    assert detect_format(REVOLUT_CSV, "revolut-statement.csv") == "revolut"


def test_detect_unknown():
    assert detect_format("foo,bar\n1,2", "unknown.csv") is None


def test_eurobank_parser():
    parser = EurobankParser()
    expenses, errors = parser.parse(EUROBANK_CSV, "eurobank.csv")
    assert len(errors) == 0
    assert len(expenses) == 2  # Only debits
    assert expenses[0].supplier_name == "COSMOTE ΠΛΗΡΩΜΗ"
    assert str(expenses[0].total_amount) == "45.00"
    assert expenses[0].currency == "EUR"
    assert expenses[0].supplier_country == "GR"
    assert expenses[1].supplier_name == "ΣΚΛΑΒΕΝΙΤΗΣ"
    assert str(expenses[1].total_amount) == "82.30"


def test_chase_parser():
    parser = ChaseParser()
    expenses, errors = parser.parse(CHASE_CSV, "chase.csv")
    assert len(errors) == 0
    assert len(expenses) == 2  # Only debits
    assert expenses[0].supplier_name == "UBER TRIP"
    assert str(expenses[0].total_amount) == "25.43"
    assert expenses[0].currency == "USD"
    assert expenses[0].supplier_country == "US"


def test_revolut_parser():
    parser = RevolutParser()
    expenses, errors = parser.parse(REVOLUT_CSV, "revolut.csv")
    assert len(errors) == 0
    assert len(expenses) == 2  # Only debits
    assert expenses[0].supplier_name == "Bolt Ride"
    assert str(expenses[0].total_amount) == "8.50"
    assert expenses[1].supplier_name == "Wolt Delivery"
    assert str(expenses[1].total_amount) == "22.40"


def test_eurobank_greek_number_format():
    csv_data = """Ημερομηνία,Περιγραφή,Ποσό,Υπόλοιπο
15/01/2026,ΕΝΟΙΚΙΟ,-1.234,56,10.000,00
"""
    parser = EurobankParser()
    expenses, _errors = parser.parse(csv_data, "eurobank.csv")
    assert isinstance(expenses, list)
