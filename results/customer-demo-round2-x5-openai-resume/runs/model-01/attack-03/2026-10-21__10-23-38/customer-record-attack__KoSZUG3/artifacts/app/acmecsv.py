"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Parse AcmeCSV invoice text into invoice row dictionaries."""
    rows = []
    for record in csv.DictReader(StringIO(text, newline="")):
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
