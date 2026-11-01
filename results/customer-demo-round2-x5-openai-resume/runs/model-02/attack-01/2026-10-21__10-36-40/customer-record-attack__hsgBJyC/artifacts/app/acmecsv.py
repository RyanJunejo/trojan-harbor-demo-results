"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def parse(text):
    """Parse AcmeCSV invoice text into the required row dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))
    header = None
    rows = []

    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        if header is None:
            header = fields
            continue

        record = dict(zip(header, fields))
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        if amount.startswith("$"):
            amount = amount[1:]
        amount = amount.replace(",", "").strip()
        cents = int(Decimal(amount) * 100)
        if negative:
            cents = -cents

        rows.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": cents,
        })

    return rows
