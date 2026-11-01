"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_cents(value):
    """Convert an AcmeCSV currency field to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    # Commas are only thousands separators once csv has decoded the field.
    value = value.removeprefix("$").replace(",", "")
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of invoice row dictionaries."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        # csv returns an empty dict for a physically blank record.  Retain the
        # old parser's behavior of ignoring whitespace-only blank records too.
        if not record or not any(value and value.strip() for value in record.values()):
            continue
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
