"""Parse invoices in the AcmeCSV dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, unquoted customer, and integer cents."""
    reader = csv.DictReader(StringIO(text, newline=""))
    if reader.fieldnames is None:
        return []

    rows = []
    for record in reader:
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
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
