"""Parser for AcmeCSV invoice exports."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, customer, and integer amount_cents."""
    reader = csv.DictReader(StringIO(text, newline=""))
    if reader.fieldnames is None:
        return []

    rows = []
    for record in reader:
        if not any(value for value in record.values()):
            continue
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if cents != cents.to_integral_value():
            raise ValueError("amount has fractional cents")
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": int(-cents if negative else cents),
        })
    return rows
