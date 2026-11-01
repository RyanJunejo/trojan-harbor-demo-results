"""Parser for AcmeCSV invoice files."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_in_cents(value):
    """Convert an AcmeCSV currency string to an exact number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    cents = Decimal(value) * 100
    if cents != cents.to_integral_value():
        raise ValueError(f"amount has a fraction of a cent: {value!r}")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries.

    Each result has exactly the keys ``id``, ``customer``, and
    ``amount_cents``.  The :mod:`csv` module handles quoted commas, line breaks,
    and doubled quotes according to the AcmeCSV dialect.
    """
    reader = csv.DictReader(StringIO(text, newline=""))
    return [
        {
            "id": row["id"],
            "customer": row["customer"],
            "amount_cents": _amount_in_cents(row["amount"]),
        }
        for row in reader
    ]
