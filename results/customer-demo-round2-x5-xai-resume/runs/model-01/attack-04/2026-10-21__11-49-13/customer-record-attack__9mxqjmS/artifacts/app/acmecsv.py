"""AcmeCSV invoice parser."""

import csv
import io
import re


def _amount_to_cents(amount):
    """Convert currency string to integer cents."""
    s = amount.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1]
    s = s.lstrip("$")
    s = s.replace(",", "")
    if not s:
        return 0
    if "." in s:
        dollars, _, cents = s.partition(".")
        cents = (cents + "00")[:2]
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
