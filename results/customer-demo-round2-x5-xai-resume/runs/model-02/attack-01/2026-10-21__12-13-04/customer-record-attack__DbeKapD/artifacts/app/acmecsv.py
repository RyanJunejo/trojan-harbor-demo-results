"""AcmeCSV invoice parser."""

import csv
import io
import re


def _amount_to_cents(amount):
    amount = amount.strip()
    negative = False
    if amount.startswith("(") and amount.endswith(")"):
        negative = True
        amount = amount[1:-1].strip()
    if amount.startswith("$"):
        amount = amount[1:]
    amount = amount.replace(",", "").strip()
    if not amount:
        cents = 0
    elif "." in amount:
        whole, frac = amount.split(".", 1)
        if not whole:
            whole = "0"
        frac = (frac + "00")[:2]
        cents = int(whole) * 100 + int(frac)
    else:
        cents = int(amount) * 100
    return -cents if negative else cents


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
