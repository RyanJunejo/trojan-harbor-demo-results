"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
import io


def parse(text):
    """Parse AcmeCSV invoice text into the required row dictionaries."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        raw_amount = record["amount"].strip()
        negative = raw_amount.startswith("(") and raw_amount.endswith(")")
        if negative:
            raw_amount = raw_amount[1:-1].strip()
        raw_amount = raw_amount.removeprefix("$").replace(",", "").strip()
        cents = int(Decimal(raw_amount) * 100)
        if negative:
            cents = -cents
        rows.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": cents,
        })
    return rows
