"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Parse AcmeCSV invoice text into invoice row dictionaries."""
    reader = csv.reader(StringIO(text, newline=""))
    nonempty_rows = (row for row in reader if row and any(field.strip() for field in row))
    header = next(nonempty_rows, None)
    if header is None:
        return []

    rows = []
    for fields in nonempty_rows:
        record = dict(zip(header, fields))
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "")
        cents = int(Decimal(amount) * 100)
        if negative:
            cents = -cents
        rows.append({"id": record["id"], "customer": record["customer"], "amount_cents": cents})
    return rows
