"""Parse invoices using the AcmeCSV migration guide's CSV and currency rules."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, unquoted customer, and integer amount_cents."""
    rows = []
    for record in csv.DictReader(StringIO(text, newline="")):
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1]
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if negative:
            cents = -cents
        if cents != cents.to_integral_value():
            raise ValueError("Amount must be an exact number of cents")
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": int(cents),
        })
    return rows
