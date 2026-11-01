"""Parser for the AcmeCSV invoice format."""

import csv
import io
from decimal import Decimal


def _amount_in_cents(value):
    """Convert an AcmeCSV dollar amount to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    cents = Decimal(value) * 100
    if cents != cents.to_integral_value():
        raise ValueError(f"amount has fractional cents: {value!r}")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    if not text.strip():
        return []

    reader = csv.DictReader(io.StringIO(text), skipinitialspace=False)
    rows = []
    for record in reader:
        # Ignore physically blank lines while retaining whitespace in real fields.
        if record is None or all(value in (None, "") for value in record.values()):
            continue
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_in_cents(record["amount"]),
        })
    return rows
