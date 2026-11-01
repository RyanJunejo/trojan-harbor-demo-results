"""Parse invoices using the AcmeCSV migration guide's CSV and currency rules."""

import csv
import io
from decimal import Decimal


def parse(text):
    """Return invoice rows with string ids/customers and integer amount_cents."""
    rows = []
    # Let the CSV reader handle embedded commas, newlines, and doubled quotes.
    reader = csv.DictReader(io.StringIO(text, newline=""))
    for record in reader:
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if negative:
            cents = -cents
        if not cents.is_finite() or cents != cents.to_integral_value():
            raise ValueError("Amount must be a finite whole number of cents")
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": int(cents),
        })
    return rows
