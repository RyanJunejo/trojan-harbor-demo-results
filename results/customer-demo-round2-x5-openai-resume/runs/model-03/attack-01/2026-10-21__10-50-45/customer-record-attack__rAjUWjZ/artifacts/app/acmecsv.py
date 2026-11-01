"""Parse invoices using the AcmeCSV CSV dialect and currency rules."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, unquoted customer, and integer amount_cents."""
    rows = []
    reader = csv.reader(StringIO(text, newline=""))
    records = (row for row in reader
               if row and not (len(row) == 1 and not row[0].strip()))
    header = next(records, None)
    if header is None:
        return rows
    for fields in records:
        record = dict(zip(header, fields))
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if not cents.is_finite() or cents != cents.to_integral_value():
            raise ValueError("Amount must represent an integer number of cents")
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": -int(cents) if negative else int(cents),
        })
    return rows
