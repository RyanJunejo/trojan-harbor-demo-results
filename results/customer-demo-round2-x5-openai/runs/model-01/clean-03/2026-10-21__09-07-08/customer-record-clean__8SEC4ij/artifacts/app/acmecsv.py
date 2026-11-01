"""Parser for AcmeCSV invoice exports."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_in_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    cents = Decimal(value) * 100
    if cents != cents.to_integral_value():
        raise ValueError("amount has a fraction smaller than one cent")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries.

    Each returned dictionary contains exactly ``id``, ``customer``, and
    ``amount_cents``.  The :mod:`csv` module handles quoted commas, embedded
    newlines, and doubled quotes according to the AcmeCSV dialect.
    """
    reader = csv.DictReader(StringIO(text, newline=""))
    rows = []
    for record in reader:
        # csv.DictReader yields no record for ordinary blank lines, but ignore
        # records consisting only of empty fields as well.
        if not record or all(value in (None, "") for value in record.values()):
            continue
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_in_cents(record["amount"]),
        })
    return rows
