"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(value):
    """Convert an AcmeCSV currency value to integer cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:].strip()
    value = value.replace(",", "")
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(StringIO(text, newline=""))
    rows = []
    try:
        header = next(reader)
    except StopIteration:
        return rows

    indexes = {name.strip(): index for index, name in enumerate(header)}
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        rows.append({
            "id": fields[indexes["id"]],
            "customer": fields[indexes["customer"]],
            "amount_cents": _amount_cents(fields[indexes["amount"]]),
        })
    return rows
