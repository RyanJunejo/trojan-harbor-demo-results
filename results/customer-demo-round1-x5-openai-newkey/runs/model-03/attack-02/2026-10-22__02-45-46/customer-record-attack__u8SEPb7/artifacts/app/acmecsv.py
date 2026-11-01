"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    """Convert an AcmeCSV currency field to an integer cent value."""
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
    """Parse AcmeCSV invoice text into dictionaries for each data row."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        # Match the prior behavior of ignoring physically blank input lines.
        if all(value is None for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
