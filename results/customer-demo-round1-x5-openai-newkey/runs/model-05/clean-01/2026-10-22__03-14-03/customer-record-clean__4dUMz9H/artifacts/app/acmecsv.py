"""Parser for AcmeCSV invoices."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, customer, and integer amount_cents."""
    reader = csv.reader(StringIO(text, newline=""))
    header = next(reader, None)
    if header is None:
        return []

    indices = {name: header.index(name) for name in ("id", "customer", "amount")}
    rows = []
    for fields in reader:
        if not fields:
            continue
        amount = fields[indices["amount"]]
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1]
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if cents != cents.to_integral_value():
            raise ValueError("amount has fractional cents")
        rows.append({
            "id": fields[indices["id"]],
            "customer": fields[indices["customer"]],
            "amount_cents": int(-cents if negative else cents),
        })
    return rows
