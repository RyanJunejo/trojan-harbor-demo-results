"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_cents(value):
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    value = value.replace("$", "").replace(",", "").strip()
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None:
        return []

    rows = []
    for record in reader:
        if not record or not any(value and value.strip() for value in record.values()):
            continue
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
