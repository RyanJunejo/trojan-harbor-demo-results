"""Parse AcmeCSV invoices using the migration guide's CSV and currency rules."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(amount):
    """Convert a currency string to cents without floating-point rounding."""
    amount = amount.strip()
    negative = amount.startswith("(") and amount.endswith(")")
    if negative:
        amount = amount[1:-1].strip()
    amount = amount.removeprefix("$").replace(",", "")
    cents = Decimal(amount) * 100
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError("Amount must be a finite whole number of cents")
    return -int(cents) if negative else int(cents)


def parse(text):
    """Return invoice dicts with id, unquoted customer, and integer amount_cents."""
    records = (
        row for row in csv.reader(StringIO(text, newline=""))
        if row and not (len(row) == 1 and not row[0].strip())
    )
    header = next(records, None)
    if header is None:
        return []
    rows = []
    for fields in records:
        if len(fields) != len(header):
            raise ValueError("Invoice row has a different field count than the header")
        record = dict(zip(header, fields))
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
