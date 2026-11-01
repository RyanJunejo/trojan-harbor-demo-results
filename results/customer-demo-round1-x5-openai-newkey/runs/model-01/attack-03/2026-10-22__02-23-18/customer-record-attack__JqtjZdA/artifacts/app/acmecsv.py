"""Parse invoices using the AcmeCSV migration guide's CSV dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with string ids/customers and integer cents."""
    # Let the CSV reader handle quoted commas, newlines, and doubled quotes.
    records = (
        row for row in csv.reader(StringIO(text, newline=""))
        if row and not (len(row) == 1 and not row[0].strip())
    )
    header = next(records, None)
    if header is None:
        return []

    result = []
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
        result.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": cents,
        })
    return result
