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

    if value.startswith("$"):
        value = value[1:].strip()
    value = value.replace(",", "")

    cents = Decimal(value) * 100
    result = int(cents)
    if cents != result:
        raise ValueError(f"amount has fractional cents: {value!r}")
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"')
    records = (row for row in reader if any(field.strip() for field in row))

    try:
        header = next(records)
    except StopIteration:
        return []

    positions = {name.strip(): index for index, name in enumerate(header)}
    required = ("id", "customer", "amount")
    if any(name not in positions for name in required):
        raise ValueError("missing required AcmeCSV column")

    rows = []
    for record in records:
        if len(record) <= max(positions[name] for name in required):
            raise ValueError("incomplete AcmeCSV row")
        rows.append({
            "id": str(record[positions["id"]]),
            "customer": record[positions["customer"]],
            "amount_cents": _amount_to_cents(record[positions["amount"]]),
        })
    return rows
