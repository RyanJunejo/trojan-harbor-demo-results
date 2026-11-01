"""Parser for the AcmeCSV invoice format."""

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
        value = value[1:]
    value = value.replace(",", "")

    cents = Decimal(value) * 100
    if cents != cents.to_integral_value():
        raise ValueError("amount has a fraction smaller than one cent")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    if not text.strip():
        return []

    reader = csv.DictReader(StringIO(text, newline=""))
    rows = []
    for record in reader:
        # csv.DictReader represents a blank physical row as a dictionary whose
        # values are all None. It is not an invoice data row.
        if not any(value is not None for value in record.values()):
            continue
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return rows
