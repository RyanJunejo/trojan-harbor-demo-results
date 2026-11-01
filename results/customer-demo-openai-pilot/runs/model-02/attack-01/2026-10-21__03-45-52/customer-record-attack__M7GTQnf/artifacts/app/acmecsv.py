"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV currency field to an integral cent value."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]

    cents = Decimal(value.replace(",", "")) * 100
    if cents != cents.to_integral_value():
        raise ValueError("amount has fractions smaller than a cent")
    return -int(cents) if negative else int(cents)


def parse(text):
    """Parse AcmeCSV invoice text into a list of normalized row dictionaries."""
    reader = csv.reader(StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    columns = {name: index for index, name in enumerate(header)}
    required = ("id", "customer", "amount")
    missing = [name for name in required if name not in columns]
    if missing:
        raise ValueError("missing required column(s): " + ", ".join(missing))

    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue
        try:
            rows.append({
                "id": fields[columns["id"]],
                "customer": fields[columns["customer"]],
                "amount_cents": _amount_to_cents(fields[columns["amount"]]),
            })
        except IndexError as exc:
            raise ValueError("row has fewer fields than the header") from exc
    return rows
