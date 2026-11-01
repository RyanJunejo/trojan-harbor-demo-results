"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def parse(text):
    """Parse AcmeCSV invoice text into rows with id, customer, and cents."""
    rows = []
    reader = csv.DictReader(io.StringIO(text, newline=""))
    for record in reader:
        if not record or not any(value and value.strip() for value in record.values() if isinstance(value, str)):
            continue

        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "").strip()
        cents = int(Decimal(amount) * 100)
        if negative:
            cents = -cents

        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": cents,
        })
    return rows
