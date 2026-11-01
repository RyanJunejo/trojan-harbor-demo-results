"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    # AcmeCSV uses commas only as thousands separators within a quoted field.
    value = value.removeprefix("$").replace(",", "")
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into the required invoice row dictionaries."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        # Ignore physical blank lines while retaining quoted fields that contain
        # line breaks (which csv.reader handles as part of their record).
        if record is None or all(value is None or not value.strip() for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
