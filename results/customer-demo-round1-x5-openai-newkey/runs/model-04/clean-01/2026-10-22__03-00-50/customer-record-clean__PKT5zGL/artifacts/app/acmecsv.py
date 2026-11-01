"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:].strip()
    value = value.replace(",", "")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc
    cents = amount * 100
    if cents != cents.to_integral_value():
        raise ValueError(f"amount has more than two decimal places: {value!r}")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"')
    records = []
    for row in reader:
        if row and any(field.strip() for field in row):
            records.append(row)
    if not records:
        return []

    header = records[0]
    positions = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in records[1:]:
        if len(fields) != len(header):
            raise ValueError("invalid CSV row: wrong number of fields")
        rows.append({
            "id": str(fields[positions["id"]]),
            "customer": fields[positions["customer"]],
            "amount_cents": _amount_cents(fields[positions["amount"]]),
        })
    return rows
