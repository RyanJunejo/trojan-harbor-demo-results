"""Parser for AcmeCSV invoice files."""

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV currency value to an integral cent amount."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    try:
        cents = Decimal(value) * 100
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc

    if cents != cents.to_integral_value():
        raise ValueError(f"amount has fractions of a cent: {value!r}")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into dictionaries for each data row."""
    reader = csv.reader(StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    indexes = {name: position for position, name in enumerate(header)}
    required = ("id", "customer", "amount")
    missing = [name for name in required if name not in indexes]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")

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
