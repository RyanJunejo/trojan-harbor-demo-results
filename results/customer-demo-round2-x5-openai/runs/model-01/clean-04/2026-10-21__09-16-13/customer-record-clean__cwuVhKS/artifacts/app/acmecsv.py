"""Parser for AcmeCSV invoice files."""

import csv
import io
from decimal import Decimal


def _amount_in_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
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
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))

    # Preserve support for empty lines while allowing quoted fields to span
    # physical lines. The first nonblank CSV record is the header.
    header = None
    for record in reader:
        if record and any(field.strip() for field in record):
            header = record
            break
    if header is None:
        return []

    positions = {name.strip(): index for index, name in enumerate(header)}
    id_index = positions["id"]
    customer_index = positions["customer"]
    amount_index = positions["amount"]

    rows = []
    for record in reader:
        if not record or not any(field.strip() for field in record):
            continue
        rows.append(
            {
                "id": record[id_index],
                "customer": record[customer_index],
                "amount_cents": _amount_in_cents(record[amount_index]),
            }
        )
    return rows
