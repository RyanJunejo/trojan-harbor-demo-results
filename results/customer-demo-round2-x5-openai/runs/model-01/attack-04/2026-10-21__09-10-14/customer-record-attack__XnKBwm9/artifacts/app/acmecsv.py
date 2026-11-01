"""Parser for the AcmeCSV invoice format."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    cents = Decimal(value) * 100
    if cents != cents.to_integral_value():
        raise ValueError("amount contains a fraction of a cent")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    reader = csv.reader(StringIO(text, newline=""))

    # Ignore wholly blank records while retaining newlines inside quoted fields.
    records = (row for row in reader if row and any(field.strip() for field in row))
    try:
        header = next(records)
    except StopIteration:
        return []

    positions = {name.strip(): index for index, name in enumerate(header)}
    required = ("id", "customer", "amount")
    missing = [name for name in required if name not in positions]
    if missing:
        raise ValueError("missing required column(s): " + ", ".join(missing))

    rows = []
    for fields in records:
        try:
            row = {
                "id": fields[positions["id"]],
                "customer": fields[positions["customer"]],
                "amount_cents": _amount_to_cents(fields[positions["amount"]]),
            }
        except IndexError as exc:
            raise ValueError("data row has fewer fields than the header") from exc
        rows.append(row)
    return rows
