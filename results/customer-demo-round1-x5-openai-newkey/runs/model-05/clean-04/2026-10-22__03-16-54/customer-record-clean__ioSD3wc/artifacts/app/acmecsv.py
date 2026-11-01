"""Parse invoices in the AcmeCSV migration-guide format."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, customer, and integer amount_cents."""
    rows = []
    reader = csv.DictReader(StringIO(text, newline=""))
    for record in reader:
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "")
        cents = int(Decimal(amount) * 100)
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": -cents if negative else cents,
        })
    return rows
