"""Parser for AcmeCSV invoice exports."""

import csv
import io
from decimal import Decimal


def _amount_cents(value):
    """Convert an AcmeCSV dollar amount to an exact number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    value = value.removeprefix("$").replace(",", "")
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    if not text.strip():
        return []

    reader = csv.DictReader(io.StringIO(text), skipinitialspace=False)
    rows = []
    for record in reader:
        # Ignore physically blank rows while retaining valid empty fields.
        if record and all(value is None or value.strip() == "" for value in record.values()):
            continue
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
