"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV currency field to an integer cent amount."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    value = value.replace("$", "").replace(",", "")
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly ``id``, ``customer``, and ``amount_cents``.
    """
    reader = csv.reader(StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    indexes = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue
        rows.append(
            {
                "id": fields[indexes["id"]],
                "customer": fields[indexes["customer"]],
                "amount_cents": _amount_to_cents(fields[indexes["amount"]]),
            }
        )
    return rows
