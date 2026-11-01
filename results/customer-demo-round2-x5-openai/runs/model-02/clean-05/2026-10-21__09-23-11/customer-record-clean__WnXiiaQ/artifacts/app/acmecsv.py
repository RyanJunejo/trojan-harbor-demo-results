"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV currency field to an integer cents value."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    # The AcmeCSV format permits a leading dollar sign and comma separators.
    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of invoice row dictionaries."""
    reader = csv.DictReader(StringIO(text))
    rows = []
    for record in reader:
        # DictReader/csv.reader handles quoted commas, embedded newlines, and
        # doubled quote escapes as specified by the AcmeCSV dialect.
        if not record or all(value is None or not value.strip() for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
