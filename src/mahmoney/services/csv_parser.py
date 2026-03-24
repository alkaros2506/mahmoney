import logging

from mahmoney.parsers.chase import ChaseParser
from mahmoney.parsers.eurobank import EurobankParser
from mahmoney.parsers.revolut import RevolutParser
from mahmoney.schemas.expense import ExpenseCreate

logger = logging.getLogger(__name__)

PARSERS = [
    EurobankParser(),
    ChaseParser(),
    RevolutParser(),
]


def detect_format(content: str, filename: str) -> str | None:
    """Detect bank format from content headers and filename."""
    filename_lower = filename.lower()
    first_line = content.split("\n")[0].lower() if content else ""

    if "eurobank" in filename_lower or "ημερομηνία" in first_line:
        return "eurobank"
    if "chase" in filename_lower or "posting date" in first_line:
        return "chase"
    if "revolut" in filename_lower or "completed date" in first_line:
        return "revolut"

    return None


def parse_csv(content: str, filename: str) -> tuple[list[ExpenseCreate], list[str]]:
    """Parse a bank CSV file into expense records.

    Returns (expenses, errors).
    """
    fmt = detect_format(content, filename)
    if not fmt:
        return [], [f"Could not detect bank format for file: {filename}"]

    parser_map = {p.bank_name: p for p in PARSERS}
    parser = parser_map.get(fmt)
    if not parser:
        return [], [f"No parser for format: {fmt}"]

    return parser.parse(content, filename)
