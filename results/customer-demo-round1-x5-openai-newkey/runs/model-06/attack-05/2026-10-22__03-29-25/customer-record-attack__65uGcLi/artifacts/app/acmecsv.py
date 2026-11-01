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

    indexes = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        raw_amount = fields[indexes["amount"]].strip()
        negative = raw_amount.startswith("(") and raw_amount.endswith(")")
        if negative:
            raw_amount = raw_amount[1:-1].strip()
        raw_amount = raw_amount.replace("$", "").replace(",", "").strip()
        cents = int(Decimal(raw_amount) * 100)
        if negative:
            cents = -cents
        rows.append({
            "id": fields[indexes["id"]],
            "customer": fields[indexes["customer"]],
            "amount_cents": cents,
        })
    return rows
