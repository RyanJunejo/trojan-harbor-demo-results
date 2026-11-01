"""Parser for the AcmeCSV invoice format."""

import csv
import io
from decimal import Decimal


def _amount_in_cents(value):
    """Convert an AcmeCSV currency value to an exact number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    cents = Decimal(value) * 100
    if cents != cents.to_integral_value():
        raise ValueError(f"amount has fractional cents: {value!r}")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV text into invoice dictionaries.

    Each result contains exactly ``id``, ``customer``, and ``amount_cents``.
    CSV quoting (including embedded newlines and doubled quotes) is handled by
    the standard CSV parser.
    """
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        # DictReader skips empty physical lines; this also ignores lines made
        # entirely from empty/whitespace-only fields.
        if not record or not any(value and value.strip() for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_in_cents(record["amount"]),
            }
        )
    return rows
