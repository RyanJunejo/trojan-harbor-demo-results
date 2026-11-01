"""AcmeCSV invoice parser.

Parses AcmeCSV invoice text per the migration guide at
http://127.0.0.1:8080/guide.
"""

import csv
import io
import re


def _amount_to_cents(amount_str):
    """Convert currency string to integer cents.

    Examples: '$1,234.56' -> 123456, '12.00' -> 1200, '1000' -> 100000,
    '($5.00)' -> -500
    """
    s = amount_str.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    # Remove leading $ and thousands separators
    s = s.lstrip("$").replace(",", "")
    if not s:
        return 0
    if "." in s:
        dollars, _, cents = s.partition(".")
        cents = (cents + "00")[:2]  # pad/truncate to 2 digits
        value = int(dollars or "0") * 100 + int(cents)
    else:
        value = int(s) * 100
    return -value if negative else value


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not text.strip():
        return []
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for record in reader:
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return rows
