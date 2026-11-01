"""Parse invoices using the AcmeCSV migration-guide dialect."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(amount):
    """Convert a currency string to cents without floating-point rounding."""
    amount = amount.strip()
    negative = amount.startswith("(") and amount.endswith(")")
    if negative:
        amount = amount[1:-1].strip()
    if amount.startswith("$"):
        amount = amount[1:]
    cents = Decimal(amount.replace(",", "")) * 100
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError("Amount must represent an integer number of cents")
    return -int(cents) if negative else int(cents)


def parse(text):
    """Return invoice rows with id, unquoted customer, and amount_cents."""
    reader = csv.DictReader(StringIO(text, newline=""))
    return [
        {
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        }
        for record in reader
    ]
