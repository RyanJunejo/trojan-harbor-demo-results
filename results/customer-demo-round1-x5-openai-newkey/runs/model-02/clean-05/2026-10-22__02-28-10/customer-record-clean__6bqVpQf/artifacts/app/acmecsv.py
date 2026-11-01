"""Parser for AcmeCSV invoice files."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(value):
    """Convert an AcmeCSV currency string to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    reader = csv.DictReader(StringIO(text, newline=""))
    rows = []
    for record in reader:
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_cents(record["amount"]),
            }
        )
    return rows
