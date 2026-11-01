"""Parse invoices using the AcmeCSV migration-guide dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with string ids, decoded names, and integer cents."""
    # Parse the entire stream so quoted fields can contain line breaks.
    records = csv.DictReader(StringIO(text, newline=""))
    rows = []
    for record in records:
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1]
        amount = amount.removeprefix("$").replace(",", "")
        cents = int(Decimal(amount) * 100)
        if negative:
            cents = -cents
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": cents,
        })
    return rows
