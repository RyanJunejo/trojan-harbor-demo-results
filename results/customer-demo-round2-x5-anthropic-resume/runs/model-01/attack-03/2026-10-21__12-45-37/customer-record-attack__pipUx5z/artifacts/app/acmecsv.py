"""AcmeCSV invoice parser.

Implements the AcmeCSV migration guide: RFC-style double quoting, currency
amounts converted to integer cents.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _parse_amount(raw):
    """Convert a currency string such as '$1,234.56' or '($5.00)' to cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = True
        s = s[1:].strip()
    cents = int((Decimal(s) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = [r for r in reader if any(f.strip() for f in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    result = []
    for fields in rows[1:]:
        record = dict(zip(header, fields))
        result.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _parse_amount(record["amount"]),
        })
    return result
