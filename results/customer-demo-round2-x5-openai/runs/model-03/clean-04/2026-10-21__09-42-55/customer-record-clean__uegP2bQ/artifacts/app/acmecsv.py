"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_cents(value):
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
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    # Ignore leading blank records, matching the format's treatment of blank lines.
    while header and not any(field.strip() for field in header):
        try:
            header = next(reader)
        except StopIteration:
            return []

    indexes = {name.strip(): index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue
        row = {
            "id": fields[indexes["id"]],
            "customer": fields[indexes["customer"]],
            "amount_cents": _amount_cents(fields[indexes["amount"]]),
        }
        rows.append(row)
    return rows
