"""AcmeCSV invoice parser."""

import csv
import io
import re


def _amount_to_cents(amount):
    """Convert an AcmeCSV currency string to integer cents."""
    s = amount.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
    if not s:
        raise ValueError(f"empty amount: {amount!r}")
    if "." in s:
        dollars, cents = s.split(".", 1)
        if dollars == "":
            dollars = "0"
        if len(cents) < 2:
            cents = cents.ljust(2, "0")
        elif len(cents) > 2:
            extra = cents[2:]
            cents = cents[:2]
            # ignore extra fractional digits beyond cents
            _ = extra
        value = int(dollars) * 100 + int(cents)
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
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
