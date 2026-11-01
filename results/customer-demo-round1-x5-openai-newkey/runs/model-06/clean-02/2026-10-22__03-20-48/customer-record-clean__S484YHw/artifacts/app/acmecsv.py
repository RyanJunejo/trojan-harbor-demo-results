"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        if not record or all(value is None or not value.strip() for value in record.values()):
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
