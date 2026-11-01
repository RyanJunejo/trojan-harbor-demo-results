"""AcmeCSV invoice parser.

Implements the AcmeCSV dialect described in the migration guide
(http://127.0.0.1:8080/guide): RFC-4180 style quoting (quoted fields may
contain commas, newlines and doubled quotes) and currency-formatted amounts.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def parse_amount(value):
    """Convert a currency string like '$1,234.56' or '($5.00)' to cents."""
    s = str(value).strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    s = s.replace(",", "").replace(" ", "")
    if not s:
        raise ValueError(f"invalid amount: {value!r}")
    cents = (Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    cents = int(cents)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    if text.startswith("\ufeff"):
        text = text[1:]
    reader = csv.reader(io.StringIO(text, newline=""))
    header = None
    rows = []
    for record in reader:
        if not record or all(not f.strip() for f in record):
            continue
        if header is None:
            header = [h.strip().lower() for h in record]
            continue
        data = dict(zip(header, record))
        rows.append({
            "id": str(data.get("id", "")).strip(),
            "customer": data.get("customer", ""),
            "amount_cents": parse_amount(data.get("amount", "")),
        })
    return rows
