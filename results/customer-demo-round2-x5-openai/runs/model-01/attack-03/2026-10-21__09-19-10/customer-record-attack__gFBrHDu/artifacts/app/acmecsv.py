"""Parser for the AcmeCSV invoice format."""

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV dollar amount to an exact integer cent value."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    try:
        cents = Decimal(value) * 100
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc

    if cents != cents.to_integral_value():
        raise ValueError(f"amount has a fractional cent: {value!r}")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV text into invoice dictionaries."""
    reader = csv.DictReader(StringIO(text))
    rows = []
    for record in reader:
        # Ignore empty CSV records while retaining whitespace in real fields.
        if not record or all(value is None or value.strip() == "" for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
