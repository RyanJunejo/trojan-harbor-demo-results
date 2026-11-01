"""AcmeCSV invoice parser.

Implements the AcmeCSV dialect described in the migration guide:
- comma-separated fields, optionally double-quoted; quoted fields may contain
  commas and line breaks; a doubled quote inside a quoted field is a literal
  quote.
- amounts are currency strings like ``$1,234.56``, ``12.00``, ``1000`` or
  ``($5.00)`` (parentheses denote a negative value) and are returned as an
  integer number of cents.
"""

import csv
import io
from decimal import Decimal, InvalidOperation


def amount_to_cents(value):
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
    s = s.replace(",", "")
    if not s:
        raise ValueError("empty amount: %r" % (value,))
    try:
        cents = (Decimal(s) * 100).to_integral_value()
    except InvalidOperation:
        raise ValueError("invalid amount: %r" % (value,))
    cents = int(cents)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys: "id" (str), "customer" (str, with CSV
    quoting removed) and "amount_cents" (int).
    """
    if text is None:
        return []
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", quotechar='"',
                        doublequote=True, skipinitialspace=False)
    header = None
    rows = []
    for parts in reader:
        if not parts or all(not p.strip() for p in parts):
            continue  # skip blank lines
        if header is None:
            header = [h.strip().lower() for h in parts]
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": str(record.get("id", "")).strip(),
            "customer": record.get("customer", ""),
            "amount_cents": amount_to_cents(record.get("amount", "")),
        })
    return rows
