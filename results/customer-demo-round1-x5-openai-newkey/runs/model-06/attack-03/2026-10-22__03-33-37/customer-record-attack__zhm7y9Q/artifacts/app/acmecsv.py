"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.DictReader(StringIO(text, newline=""))
    rows = []
    for record in reader:
        if not record or all(value is None or not value.strip() for value in record.values()):
            continue

        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.replace(",", "")
        if amount.startswith("$"):
            amount = amount[1:]
        cents = int(Decimal(amount) * 100)
        if negative:
            cents = -cents

        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": cents,
        })
    return rows
