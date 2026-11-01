"""Parse invoices using the AcmeCSV migration-guide dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, unquoted customer, and integer cents."""
    reader = csv.reader(StringIO(text, newline=""))
    # Ignore blank lines outside quoted fields, without losing embedded newlines.
    header = next((row for row in reader if row and any(row)), None)
    if header is None:
        return []

    rows = []
    for fields in reader:
        if not fields or not any(fields):
            continue
        record = dict(zip(header, fields))
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if negative:
            cents = -cents
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": int(cents),
        })
    return rows
