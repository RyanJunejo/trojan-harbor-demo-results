"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    """Convert an AcmeCSV currency field to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    # AcmeCSV permits a leading dollar sign and comma thousands separators.
    value = value.removeprefix("$").replace(",", "")
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: ``id`` (str), ``customer`` (str), and
    ``amount_cents`` (int).
    """
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        # Ignore entirely blank physical CSV records, matching the prior parser.
        if record is None or not any(value for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
