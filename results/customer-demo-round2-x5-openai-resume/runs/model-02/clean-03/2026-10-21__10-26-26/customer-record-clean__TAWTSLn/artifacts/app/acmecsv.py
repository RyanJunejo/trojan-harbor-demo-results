"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Parse AcmeCSV invoice text into the required row dictionaries."""
    reader = csv.reader(StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    columns = {name.strip(): index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue

        amount = fields[columns["amount"]].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.replace("$", "").replace(",", "").strip()
        cents = int(Decimal(amount) * 100)
        if negative:
            cents = -cents

        rows.append({
            "id": str(fields[columns["id"]]),
            "customer": fields[columns["customer"]],
            "amount_cents": cents,
        })
    return rows
