"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_cents(value):
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:].strip()
    value = value.replace(",", "")
    amount = Decimal(value)
    cents = int(amount * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"')
    try:
        header = next(reader)
    except StopIteration:
        return []

    # AcmeCSV's header names identify these three fields.
    indexes = {name.strip(): index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        rows.append({
            "id": str(fields[indexes["id"]]),
            "customer": fields[indexes["customer"]],
            "amount_cents": _amount_cents(fields[indexes["amount"]]),
        })
    return rows
