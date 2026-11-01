"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    cents = int(Decimal(value.replace(",", "")) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into the required invoice row dictionaries."""
    reader = csv.DictReader(StringIO(text, newline=""))
    rows = []
    for record in reader:
        if record is None or not any(value and value.strip() for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_cents(record["amount"]),
            }
        )
    return rows
