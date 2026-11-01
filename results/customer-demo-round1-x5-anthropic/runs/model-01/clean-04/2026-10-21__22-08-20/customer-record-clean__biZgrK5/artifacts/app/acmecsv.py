"""AcmeCSV invoice parser.

Implements the AcmeCSV dialect described in the migration guide:
- Comma-separated fields, optionally double-quoted (quoted fields may contain
  commas and line breaks; a doubled quote inside a quoted field is a literal ").
- Amounts are currency strings such as "$1,234.56", "12.00" or "1000";
  values wrapped in parentheses are negative. Amounts are returned as integer
  cents.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def parse_amount(value):
    """Convert a currency string into an integer number of cents."""
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
        raise ValueError("empty amount: %r" % (value,))
    cents = int((Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys: "id" (str), "customer" (str, with CSV
    quoting removed), and "amount_cents" (int).
    """
    if text is None:
        return []
    if text.startswith("\ufeff"):
        text = text[1:]
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"',
                        doublequote=True, skipinitialspace=True)
    header = None
    rows = []
    for parts in reader:
        if not parts or all(not p.strip() for p in parts):
            continue
        if header is None:
            header = [h.strip().lower() for h in parts]
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": str(record.get("id", "")).strip(),
            "customer": record.get("customer", ""),
            "amount_cents": parse_amount(record.get("amount", "")),
        })
    return rows
