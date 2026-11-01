"""Parser for the AcmeCSV invoice format."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_in_cents(raw):
    """Convert an AcmeCSV currency string to an exact integer cent value."""
    value = raw.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    try:
        cents = Decimal(value) * 100
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {raw!r}") from exc

    integral_cents = cents.to_integral_value()
    if cents != integral_cents:
        raise ValueError(f"amount has fractional cents: {raw!r}")

    result = int(integral_cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        if not record or all(value in (None, "") for value in record.values()):
            continue
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_in_cents(record["amount"]),
        })
    return rows
