"""AcmeCSV invoice parser.

Parses AcmeCSV per the migration guide at http://127.0.0.1:8080/guide:
RFC-4180-style quoting (doubled quotes, embedded commas/newlines) and
currency-formatted amounts ($1,234.56, 12.00, 1000, ($5.00) negative).
"""
import csv
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _parse_amount(raw):
    """Convert a currency string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    try:
        value = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {raw!r}") from exc
    cents = int((value * 100).to_integral_value(rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows_iter = (row for row in reader if any(field.strip() for field in row))
    try:
        header = [h.strip() for h in next(rows_iter)]
    except StopIteration:
        return []
    idx_id = header.index("id")
    idx_customer = header.index("customer")
    idx_amount = header.index("amount")
    rows = []
    for fields in rows_iter:
        rows.append({
            "id": fields[idx_id].strip(),
            "customer": fields[idx_customer],
            "amount_cents": _parse_amount(fields[idx_amount]),
        })
    return rows
