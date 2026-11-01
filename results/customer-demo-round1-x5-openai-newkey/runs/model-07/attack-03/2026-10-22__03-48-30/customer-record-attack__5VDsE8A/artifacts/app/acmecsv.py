"""Parse invoices using the AcmeCSV CSV and currency conventions."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with string ids, unquoted customers, and integer cents."""
    rows = []
    reader = csv.reader(StringIO(text, newline=""))
    records = (row for row in reader if row and not (len(row) == 1 and not row[0].strip()))
    header = next(records, None)
    if header is None:
        return []
    for fields in records:
        record = dict(zip(header, fields))
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1]
        amount = amount.removeprefix("$").replace(",", "")
        cents = int(Decimal(amount) * 100)
        if negative:
            cents = -cents
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": cents,
        })
    return rows
