"""Parser for the AcmeCSV invoice format."""

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    """Convert an AcmeCSV dollar amount to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")
    cents = Decimal(value) * 100
    if cents != cents.to_integral_value():
        raise ValueError("amount has fractional cents")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))

    try:
        header = next(reader)
    except StopIteration:
        return []

    # Tolerate blank lines before the header while retaining CSV-aware parsing.
    while not any(field.strip() for field in header):
        try:
            header = next(reader)
        except StopIteration:
            return []

    indexes = {name.strip(): index for index, name in enumerate(header)}
    required = ("id", "customer", "amount")
    missing = [name for name in required if name not in indexes]
    if missing:
        raise ValueError("missing required column(s): " + ", ".join(missing))

    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue
        try:
            rows.append({
                "id": fields[indexes["id"]],
                "customer": fields[indexes["customer"]],
                "amount_cents": _amount_to_cents(fields[indexes["amount"]]),
            })
        except IndexError as exc:
            raise ValueError("row has fewer fields than the header") from exc
    return rows
