"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_to_cents(value):
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    value = value.replace("$", "").replace(",", "").strip()
    amount_cents = Decimal(value) * 100
    if amount_cents != amount_cents.to_integral_value():
        raise ValueError(f"amount has fractions of a cent: {value!r}")
    cents = int(amount_cents)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    indexes = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        rows.append({
            "id": str(fields[indexes["id"]]),
            "customer": fields[indexes["customer"]],
            "amount_cents": _amount_to_cents(fields[indexes["amount"]]),
        })
    return rows
