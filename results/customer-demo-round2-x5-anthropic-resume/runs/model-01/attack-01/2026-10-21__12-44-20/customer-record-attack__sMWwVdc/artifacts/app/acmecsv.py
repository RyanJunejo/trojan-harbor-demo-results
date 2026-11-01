"""AcmeCSV invoice parser.

Follows the AcmeCSV migration guide: standard CSV quoting (commas and doubled
quotes inside quoted fields) and currency-formatted amounts.
"""
import csv
import io
from decimal import Decimal


def _parse_amount(raw):
    """Convert an amount string like $1,234.56 or ($5.00) to integer cents."""
    s = raw.strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        neg = not neg
        s = s[1:].strip()
    cents = int((Decimal(s) * 100).to_integral_value())
    return -cents if neg else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    rows_raw = [r for r in csv.reader(io.StringIO(text)) if any(f.strip() for f in r)]
    if not rows_raw:
        return []
    header = [h.strip() for h in rows_raw[0]]
    rows = []
    for parts in rows_raw[1:]:
        record = dict(zip(header, parts))
        rows.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _parse_amount(record["amount"]),
        })
    return rows
