"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    # AcmeCSV uses commas only as thousands separators and an optional $ sign.
    value = value.replace("$", "").replace(",", "")
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly ``id``, ``customer``, and ``amount_cents``.
    """
    reader = csv.DictReader(StringIO(text, newline=""))
    rows = []
    for record in reader:
        # Ignore entirely blank physical records while retaining valid empty fields.
        if not record or not any(value not in (None, "") for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
