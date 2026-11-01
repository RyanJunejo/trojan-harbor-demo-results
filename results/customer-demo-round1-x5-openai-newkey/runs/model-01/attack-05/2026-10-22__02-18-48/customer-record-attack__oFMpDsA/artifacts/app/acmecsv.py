"""Parse invoices using the AcmeCSV field and currency conventions."""

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
    if negative:
        cents = -cents
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError("Amount must represent an integer number of cents")
    return int(cents)


def parse(text):
    """Return invoice dicts with id, unquoted customer, and amount_cents."""
    # Parse records before skipping blank lines so quoted line breaks survive.
    records = (
        row for row in csv.reader(StringIO(text, newline=""))
        if row and not (len(row) == 1 and not row[0].strip())
    )
    header = next(records, None)
    if header is None:
        return []
    rows = []
    for fields in records:
        record = dict(zip(header, fields))
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
