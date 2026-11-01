"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:].strip()
    value = value.replace(",", "")
    cents = Decimal(value) * 100
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(StringIO(text), delimiter=",", quotechar='"')
    try:
        header = next(reader)
    except StopIteration:
        return []

    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue
        record = dict(zip(header, fields))
        rows.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return rows
