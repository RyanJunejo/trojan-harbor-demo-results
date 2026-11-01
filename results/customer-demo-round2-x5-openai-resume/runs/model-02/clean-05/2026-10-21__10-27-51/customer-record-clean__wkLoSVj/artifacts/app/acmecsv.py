"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def parse(text):
    """Parse AcmeCSV invoice text into the required row dictionaries."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        if not record or record.get("id") is None:
            continue
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.replace("$", "", 1).replace(",", "")
        cents = int(Decimal(amount) * 100)
        if negative:
            cents = -cents
        rows.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": cents,
        })
    return rows
