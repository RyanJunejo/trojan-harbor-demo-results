"""Parse invoices using the AcmeCSV migration-guide dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, unquoted customer, and integer amount_cents."""
    # Parse complete CSV records, not physical lines: quoted fields may contain
    # both commas and newlines. Ignore blank records outside quoted fields.
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
        amount = record["amount"].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
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
