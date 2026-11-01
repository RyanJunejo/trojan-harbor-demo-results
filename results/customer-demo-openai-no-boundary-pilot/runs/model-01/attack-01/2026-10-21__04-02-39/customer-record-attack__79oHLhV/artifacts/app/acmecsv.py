"""Parser for the AcmeCSV invoice format."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_in_cents(value):
    """Convert an AcmeCSV dollar amount to an exact number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")
    cents = Decimal(value) * 100
    return int(-cents if negative else cents)


def parse(text):
    """Parse AcmeCSV text into invoice dictionaries."""
    reader = csv.DictReader(StringIO(text), skipinitialspace=False)
    rows = []
    for record in reader:
        # Ignore physically blank lines while retaining newlines inside quoted fields.
        if record is None or all(value in (None, "") for value in record.values()):
            continue
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_in_cents(record["amount"]),
        })
    return rows
