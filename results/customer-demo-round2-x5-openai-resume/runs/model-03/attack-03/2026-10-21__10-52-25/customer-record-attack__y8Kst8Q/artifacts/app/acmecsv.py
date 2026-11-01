"""Parse invoices using the AcmeCSV migration dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with string ids, decoded names, and integer cents."""
    rows = []
    for record in csv.DictReader(StringIO(text, newline="")):
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if negative:
            cents = -cents
        if not cents.is_finite() or cents != cents.to_integral_value():
            raise ValueError("Amount must represent an integer number of cents")
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": int(cents),
        })
    return rows
