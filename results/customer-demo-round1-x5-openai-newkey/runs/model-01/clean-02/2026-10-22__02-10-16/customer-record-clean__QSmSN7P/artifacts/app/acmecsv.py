"""Parse invoices using the AcmeCSV migration-guide dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with string ids, customers, and integer cents."""
    reader = csv.reader(StringIO(text, newline=""))
    # Skip empty records, but never split or discard lines inside quoted fields.
    records = (row for row in reader if row and any(value.strip() for value in row))
    header = next(records, None)
    if header is None:
        return []

    rows = []
    for fields in records:
        record = dict(zip(header, fields))
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
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
