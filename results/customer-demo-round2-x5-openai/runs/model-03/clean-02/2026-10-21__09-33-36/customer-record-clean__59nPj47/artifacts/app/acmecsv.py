"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_cents(value):
    """Convert an AcmeCSV currency value to integer cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "").strip()
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    rows = []
    reader = csv.reader(io.StringIO(text), strict=True)
    try:
        header = next(reader)
    except StopIteration:
        return rows

    # Ignore completely empty records, matching the parser's prior behavior.
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
