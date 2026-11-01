"""AcmeCSV invoice parser."""

import csv
import io
import re


def _amount_to_cents(raw):
    """Convert an AcmeCSV currency string to integer cents."""
    s = raw.strip()
    if not s:
        raise ValueError("empty amount")

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    if s.startswith("$"):
        s = s[1:].strip()

    s = s.replace(",", "")

    if s.startswith("-"):
        negative = True
        s = s[1:].strip()

    if "." in s:
        dollars, cents = s.split(".", 1)
        if dollars == "":
            dollars = "0"
        if not dollars.isdigit() or not cents.isdigit() or len(cents) > 2:
            # allow exactly two-digit cents; pad if one digit
            if not dollars.isdigit() or not cents.isdigit():
                raise ValueError(f"invalid amount: {raw!r}")
        cents = (cents + "00")[:2]
        value = int(dollars) * 100 + int(cents)
    else:
        if not s.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
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
