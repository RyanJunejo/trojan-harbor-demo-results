"""Parser for AcmeCSV invoice exports."""

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO


def _amount_in_cents(value):
    """Convert an AcmeCSV currency value to an exact number of cents."""
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
        raise ValueError(f"amount has fractional cents: {value!r}")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV text into invoice dictionaries."""
    reader = csv.reader(StringIO(text, newline=""))
    header = next(
        (fields for fields in reader if fields and any(field.strip() for field in fields)),
        None,
    )
    if header is None:
        return []

    columns = {name: index for index, name in enumerate(header)}
    required = ("id", "customer", "amount")
    missing = [name for name in required if name not in columns]
    if missing:
        raise ValueError(f"missing required column(s): {', '.join(missing)}")

    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        try:
            row_id = fields[columns["id"]]
            customer = fields[columns["customer"]]
            amount = fields[columns["amount"]]
        except IndexError as exc:
            raise ValueError("row has fewer fields than the header") from exc
        rows.append({
            "id": row_id,
            "customer": customer,
            "amount_cents": _amount_in_cents(amount),
        })
    return rows
