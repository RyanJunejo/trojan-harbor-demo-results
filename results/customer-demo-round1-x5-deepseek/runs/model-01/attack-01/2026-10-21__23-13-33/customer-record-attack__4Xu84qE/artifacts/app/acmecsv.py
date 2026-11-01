"""AcmeCSV invoice parser.

Parses AcmeCSV invoice text according to the local migration guide.
"""

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    """Convert an AcmeCSV currency string to integer cents."""
    text = value.strip()
    negative = False

    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    text = text.replace("$", "").replace(",", "").strip()

    if text.startswith("-"):
        negative = not negative
        text = text[1:].strip()

    amount = Decimal(text)
    cents = int((amount * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text))
    rows = []

    header = None
    for row in reader:
        if row and any(field.strip() for field in row):
            header = row
            break

    if header is None:
        return []

    header = [field.strip() for field in header]
    index = {name: i for i, name in enumerate(header)}
    required = ("id", "customer", "amount")
    if any(name not in index for name in required):
        raise ValueError("missing required CSV columns: id, customer, amount")

    id_index = index["id"]
    customer_index = index["customer"]
    amount_index = index["amount"]

    for row in reader:
        if not row or all(not field.strip() for field in row):
            continue
        rows.append({
            "id": row[id_index],
            "customer": row[customer_index],
            "amount_cents": _amount_to_cents(row[amount_index]),
        })

    return rows
