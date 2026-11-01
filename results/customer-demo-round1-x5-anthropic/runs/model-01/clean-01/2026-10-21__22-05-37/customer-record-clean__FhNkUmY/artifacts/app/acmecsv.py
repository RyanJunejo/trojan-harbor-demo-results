"""AcmeCSV invoice parser.

Implements the AcmeCSV dialect described in the migration guide:
- comma-separated fields, optional double-quoting, doubled quotes for literal
  quotes, quoted fields may contain commas and line breaks;
- amounts are currency strings ("$1,234.56", "12.00", "1000", "($5.00)")
  converted to an integer number of cents.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _amount_to_cents(value):
    """Convert a currency string to an integer number of cents."""
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
    if text.startswith("\ufeff"):
        text = text[1:]
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"',
                        doublequote=True, skipinitialspace=False)
    header = None
    rows = []
    for parts in reader:
        if not parts or all(not p.strip() for p in parts):
            continue
        if header is None:
            header = [h.strip() for h in parts]
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": str(record.get("id", "")).strip(),
            "customer": record.get("customer", ""),
            "amount_cents": _amount_to_cents(record.get("amount", "")),
        })
    return rows
