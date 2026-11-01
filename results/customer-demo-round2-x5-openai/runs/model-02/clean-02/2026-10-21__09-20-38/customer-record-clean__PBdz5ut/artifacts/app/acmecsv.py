"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Parse AcmeCSV invoice text into Acme invoice row dictionaries."""
    reader = csv.DictReader(StringIO(text))
    rows = []
    for record in reader:
        # DictReader represents blank CSV records as dictionaries of empty
        # fields; ignore those while retaining fields that contain newlines.
        if not record or not any(value for value in record.values()):
            continue

        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        if amount.startswith("$"):
            amount = amount[1:]
        cents = int(Decimal(amount.replace(",", "")) * 100)
        if negative:
            cents = -cents

        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": cents,
        })
    return rows
