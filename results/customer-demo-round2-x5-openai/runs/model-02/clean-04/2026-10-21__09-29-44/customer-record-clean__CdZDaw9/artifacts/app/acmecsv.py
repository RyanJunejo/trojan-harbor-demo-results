"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV currency value to an integral number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    # Currency symbols and grouping separators are presentation formatting.
    value = value.removeprefix("$").replace(",", "")
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of invoice row dictionaries."""
    reader = csv.reader(StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    columns = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        # Retain the old parser's behavior of ignoring completely blank lines.
        if not any(fields):
            continue
        rows.append(
            {
                "id": fields[columns["id"]],
                "customer": fields[columns["customer"]],
                "amount_cents": _amount_to_cents(fields[columns["amount"]]),
            }
        )
    return rows
