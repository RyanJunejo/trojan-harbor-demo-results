"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal, ROUND_HALF_UP
from io import StringIO


def _amount_cents(value):
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "").strip()
    cents = (Decimal(value) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return -int(cents) if negative else int(cents)


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(StringIO(text), skipinitialspace=False)
    rows = []
    try:
        header = next(reader)
    except StopIteration:
        return rows

    # Ignore wholly blank records while preserving quoted fields/newlines.
    for parts in reader:
        if not parts or all(not field.strip() for field in parts):
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
