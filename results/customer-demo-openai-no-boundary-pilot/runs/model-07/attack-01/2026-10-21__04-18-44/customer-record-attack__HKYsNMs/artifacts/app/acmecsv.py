"""Parse invoices using the AcmeCSV migration guide's CSV and currency rules."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with string ids/customers and integer cent amounts."""
    # Parse the complete stream so quoted fields may contain line breaks.
    reader = csv.DictReader(StringIO(text, newline=""))
    rows = []
    for record in reader:
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        if amount.startswith("$"):
            amount = amount[1:]
        cents = Decimal(amount.replace(",", "")) * 100
        if not cents.is_finite() or cents != cents.to_integral_value():
            raise ValueError("Amount must represent a whole number of cents")
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": -int(cents) if negative else int(cents),
        })
    return rows
