"""Parser for the AcmeCSV invoice format."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_to_cents(value):
    """Convert an AcmeCSV currency string to an integer number of cents."""
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

    # Currency values must resolve to a whole number of cents.
    if cents != cents.to_integral_value():
        raise ValueError(f"amount has fractional cents: {value!r}")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))

    header = None
    for fields in reader:
        if fields and any(field.strip() for field in fields):
            header = fields
            break
    if header is None:
        return []

    required = ("id", "customer", "amount")
    missing = [name for name in required if name not in header]
    if missing:
        raise ValueError(f"missing required column(s): {', '.join(missing)}")

    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue
        if len(fields) != len(header):
            raise ValueError(
                f"CSV row has {len(fields)} fields; expected {len(header)}"
            )
        record = dict(zip(header, fields))
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
