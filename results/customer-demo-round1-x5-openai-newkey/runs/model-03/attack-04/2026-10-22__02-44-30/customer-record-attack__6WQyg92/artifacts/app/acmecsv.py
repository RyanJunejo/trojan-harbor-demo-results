"""Parser for AcmeCSV invoice exports."""

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    """Convert an AcmeCSV currency value into an integer cent amount."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    cents = int(Decimal(value.replace(",", "")) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into normalized invoice dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    columns = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or not any(fields):
            continue
        rows.append(
            {
                "id": fields[columns["id"]],
                "customer": fields[columns["customer"]],
                "amount_cents": _amount_to_cents(fields[columns["amount"]]),
            }
        )
    return rows
