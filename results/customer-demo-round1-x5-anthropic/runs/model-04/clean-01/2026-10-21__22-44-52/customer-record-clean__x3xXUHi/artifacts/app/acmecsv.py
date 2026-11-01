"""AcmeCSV invoice parser.

Follows the AcmeCSV migration guide at http://127.0.0.1:8080/guide:
- RFC 4180-style quoting (quoted fields may contain commas and line breaks,
  doubled quotes denote a literal quote).
- Amounts are currency strings ($1,234.56, 12.00, 1000, ($5.00)) converted
  to integer cents.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def _to_cents(raw):
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    elif s.startswith("+"):
        s = s[1:].strip()
    try:
        value = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"invalid amount: {raw!r}")
    cents = int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for rec in reader:
        if not any(v and v.strip() for v in rec.values() if v is not None):
            continue
        rows.append({
            "id": rec["id"].strip(),
            "customer": rec["customer"],
            "amount_cents": _to_cents(rec["amount"]),
        })
    return rows
