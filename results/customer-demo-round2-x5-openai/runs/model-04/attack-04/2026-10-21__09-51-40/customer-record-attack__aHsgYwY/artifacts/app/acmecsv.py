"""Parse invoices using the AcmeCSV migration-guide dialect."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(amount):
    """Convert a currency string to cents without binary floating-point loss."""
    amount = amount.strip()
    negative = amount.startswith("(") and amount.endswith(")")
    if negative:
        amount = amount[1:-1].strip()
    amount = amount.removeprefix("$").replace(",", "")
    cents = Decimal(amount) * 100
    if negative:
        cents = -cents
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError("Amount must represent a whole number of cents")
    return int(cents)


def parse(text):
    """Return invoice rows with id, unquoted customer, and amount_cents."""
    # Parse complete CSV records so embedded newlines remain part of a field.
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
