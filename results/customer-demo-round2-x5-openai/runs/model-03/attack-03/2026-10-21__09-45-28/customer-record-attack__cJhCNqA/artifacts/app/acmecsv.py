"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text), dialect="excel")
    try:
        header = next(reader)
    except StopIteration:
        return []

    rows = []
    for parts in reader:
        if not parts or all(not field.strip() for field in parts):
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return rows
