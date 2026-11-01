"""Parse invoices using the AcmeCSV migration dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, unquoted customer, and integer cents."""
    reader = csv.reader(StringIO(text, newline=""))
    # Ignore blank records without discarding newlines inside quoted fields.
    records = (row for row in reader
               if row and not (len(row) == 1 and not row[0].strip()))
    header = next(records, None)
    if header is None:
        return []

    rows = []
    for fields in records:
        if len(fields) != len(header):
            raise ValueError("Invoice row does not match the CSV header")
        record = dict(zip(header, fields))
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if not cents.is_finite() or cents != cents.to_integral_value():
            raise ValueError("Invoice amount must represent whole cents")
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": -int(cents) if negative else int(cents),
        })
    return rows
