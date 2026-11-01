"""Parser for AcmeCSV invoice files."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_in_cents(value):
    """Convert an AcmeCSV dollar amount to an exact number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")
    cents = Decimal(value) * 100
    if cents != cents.to_integral_value():
        raise ValueError("amount has a fractional cent")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV text into invoice dictionaries."""
    reader = csv.reader(StringIO(text), delimiter=",", quotechar='"',
                        doublequote=True)
    try:
        header = next(reader)
    except StopIteration:
        return []

    columns = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        rows.append({
            "id": fields[columns["id"]],
            "customer": fields[columns["customer"]],
            "amount_cents": _amount_in_cents(fields[columns["amount"]]),
        })
    return rows
