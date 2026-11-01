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

    value = value.removeprefix("$").replace(",", "")
    cents = Decimal(value) * 100
    if cents != cents.to_integral_value():
        raise ValueError("amount has a fractional cent")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV text into invoice dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))

    try:
        header = next(reader)
    except StopIteration:
        return []

    columns = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        rows.append(
            {
                "id": fields[columns["id"]],
                "customer": fields[columns["customer"]],
                "amount_cents": _amount_in_cents(fields[columns["amount"]]),
            }
        )
    return rows
