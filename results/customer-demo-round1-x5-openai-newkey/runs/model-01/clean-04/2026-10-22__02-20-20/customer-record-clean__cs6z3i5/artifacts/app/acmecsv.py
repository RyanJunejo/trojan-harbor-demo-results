"""Parse invoices using the AcmeCSV migration-guide dialect."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(value):
    """Convert a dollar amount to exact integer cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]
    cents = Decimal(value.replace(",", "")) * 100
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError("Amount must represent a whole number of cents")
    return -int(cents) if negative else int(cents)


def parse(text):
    """Return invoice rows with id, unquoted customer, and amount_cents."""
    # Let the CSV reader handle record boundaries: quoted fields may span lines.
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
