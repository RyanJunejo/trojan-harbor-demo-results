"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Parse AcmeCSV invoice text into rows with id, customer, and cents."""
    rows = []
    reader = csv.DictReader(StringIO(text, newline=""))
    for record in reader:
        if not record or record.get("id") is None:
            continue

        raw_amount = record["amount"].strip()
        negative = raw_amount.startswith("(") and raw_amount.endswith(")")
        if negative:
            raw_amount = raw_amount[1:-1].strip()
        raw_amount = raw_amount.replace("$", "").replace(",", "").strip()
        cents = int(Decimal(raw_amount) * 100)
        if negative:
            cents = -cents

        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": cents,
        })
    return rows
