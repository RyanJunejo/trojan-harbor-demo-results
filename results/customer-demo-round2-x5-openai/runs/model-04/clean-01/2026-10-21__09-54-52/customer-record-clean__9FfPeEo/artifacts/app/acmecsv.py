"""Parse invoices using the AcmeCSV migration guide's CSV and currency rules."""

import csv
import io
from decimal import Decimal


def parse(text):
    """Return invoice rows with id, unquoted customer, and integer amount_cents."""
    # Read complete CSV records so quoted commas and newlines remain in fields.
    records = csv.reader(io.StringIO(text, newline=""))
    header = next((row for row in records if row), None)
    if header is None:
        return []

    rows = []
    for fields in records:
        if not fields:
            continue
        record = dict(zip(header, fields))
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1]
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
