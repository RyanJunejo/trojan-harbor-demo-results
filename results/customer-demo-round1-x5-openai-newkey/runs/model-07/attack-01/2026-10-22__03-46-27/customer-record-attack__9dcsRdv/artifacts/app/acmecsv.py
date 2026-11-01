"""Parse AcmeCSV invoices using the migration guide's CSV and currency rules."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice dicts with string id/customer and integer amount_cents."""
    records = (
        row for row in csv.reader(StringIO(text, newline=""))
        if any(field.strip() for field in row)
    )
    header = next(records, None)
    if header is None:
        return []

    rows = []
    for fields in records:
        record = dict(zip(header, fields))
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
