"""AcmeCSV invoice parser.

Implements the AcmeCSV dialect described in the migration guide:
- comma-separated fields, optionally double-quoted (quoted fields may contain
  commas and line breaks; a doubled quote inside a quoted field is a literal
  quote);
- amounts are currency strings like ``$1,234.56``, ``12.00``, ``1000`` or
  ``($5.00)`` (parentheses denote a negative value) and are returned as an
  integer number of cents.
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
    if not text or not text.strip():
        return []
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"',
                        doublequote=True, skipinitialspace=True)
    header = None
    rows = []
    for record in reader:
        if not record or all(not field.strip() for field in record):
            continue
        if header is None:
            header = [h.strip() for h in record]
            continue
        data = dict(zip(header, record))
        rows.append({
            "id": str(data.get("id", "")).strip(),
            "customer": data.get("customer", ""),
            "amount_cents": parse_amount(data.get("amount", "")),
        })
    return rows
