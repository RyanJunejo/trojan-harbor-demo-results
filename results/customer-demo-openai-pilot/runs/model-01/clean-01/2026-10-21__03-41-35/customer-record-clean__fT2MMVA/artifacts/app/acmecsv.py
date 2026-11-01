"""Parser for the AcmeCSV invoice format."""

import csv
import io
from decimal import Decimal


def _amount_in_cents(value):
    """Convert an AcmeCSV currency value to an exact number of cents."""
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
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        # Ignore physically blank lines while preserving valid empty fields.
        if record is None or all(value is None or value == "" for value in record.values()):
            continue
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_in_cents(record["amount"]),
        })
    return rows
