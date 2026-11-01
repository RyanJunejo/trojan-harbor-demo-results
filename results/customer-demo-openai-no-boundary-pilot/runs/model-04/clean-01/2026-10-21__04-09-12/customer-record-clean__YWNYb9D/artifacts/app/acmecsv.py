"""Parse invoice data using the AcmeCSV migration guide's CSV dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with string ids/customers and integer cent amounts."""
    reader = csv.reader(StringIO(text, newline=""))
    # Ignore empty records, without disturbing line breaks in quoted fields.
    header = next((row for row in reader if row and not (len(row) == 1 and not row[0].strip())), None)
    if header is None:
        return []

    rows = []
    for fields in reader:
        if not fields or (len(fields) == 1 and not fields[0].strip()):
            continue
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
