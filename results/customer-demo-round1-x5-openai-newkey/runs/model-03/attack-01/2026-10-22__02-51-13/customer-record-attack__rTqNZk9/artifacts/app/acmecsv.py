"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_to_cents(value):
    """Convert an AcmeCSV currency field to an integral number of cents."""
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
        raise ValueError(f"amount is not representable in whole cents: {value!r}")

    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into the required invoice row dictionaries."""
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = []
    for record in reader:
        if record is None or not any(value not in (None, "") for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
