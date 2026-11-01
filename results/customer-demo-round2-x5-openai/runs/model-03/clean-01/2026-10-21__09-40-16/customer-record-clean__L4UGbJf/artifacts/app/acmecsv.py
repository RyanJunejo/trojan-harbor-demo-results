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
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"')
    rows = []
    header_seen = False
    for fields in reader:
        if not fields or (len(fields) == 1 and not fields[0].strip()):
            continue
        if not header_seen:
            header_seen = True
            continue
        if len(fields) < 3:
            raise ValueError("invoice row must contain id, customer, and amount")
        rows.append({
            "id": str(fields[0]),
            "customer": fields[1],
            "amount_cents": _amount_cents(fields[2]),
        })
    return rows
