"""Parse invoices using the AcmeCSV CSV and currency conventions."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(value):
    """Convert a dollar amount to cents without binary floating-point rounding."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1]
    if value.startswith("$"):
        value = value[1:]
    cents = Decimal(value.replace(",", "")) * 100
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError("Amount must be a finite whole number of cents")
    return -int(cents) if negative else int(cents)


def parse(text):
    """Return invoice dicts with string id/customer and integer amount_cents."""
    # Read logical CSV records, not physical lines: quoted fields can span lines.
    records = csv.reader(StringIO(text, newline=""))
    header = None
    rows = []
    for fields in records:
        if not fields or (len(fields) == 1 and not fields[0].strip()):
            continue
        if header is None:
            header = fields
            continue
        record = dict(zip(header, fields))
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
