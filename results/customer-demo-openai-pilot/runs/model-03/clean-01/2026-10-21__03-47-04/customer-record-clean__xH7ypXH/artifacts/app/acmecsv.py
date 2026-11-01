"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import StringIO


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
    cents = (amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return -int(cents) if negative else int(cents)


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(StringIO(text, newline=None), skipinitialspace=False)
    try:
        header = next(reader)
    except StopIteration:
        return []

    header = [field.strip() for field in header]
    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        record = dict(zip(header, fields))
        rows.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
