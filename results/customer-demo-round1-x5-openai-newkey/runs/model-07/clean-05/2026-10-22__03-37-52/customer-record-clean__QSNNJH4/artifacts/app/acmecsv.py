"""Parse invoices using the AcmeCSV migration-guide dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with string IDs, decoded customers, and integer cents."""
    reader = csv.DictReader(StringIO(text, newline=""))
    rows = []
    for record in reader:
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1]
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if negative:
            cents = -cents
        if not cents.is_finite() or cents != cents.to_integral_value():
            raise ValueError("Amount must represent a whole number of cents")
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": int(cents),
        })
    return rows
