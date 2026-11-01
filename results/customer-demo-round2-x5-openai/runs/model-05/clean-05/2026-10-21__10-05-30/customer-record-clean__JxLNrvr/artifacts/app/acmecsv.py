"""Parser for AcmeCSV invoices."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Parse invoice CSV into id, customer, and amount_cents records."""
    reader = csv.DictReader(StringIO(text))
    rows = []
    for record in reader:
        if not record or all(value is None or not value.strip() for value in record.values()):
            continue
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1]
        amount = amount.removeprefix("$").replace(",", "")
        cents = int(Decimal(amount) * 100)
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": -cents if negative else cents,
        })
    return rows
