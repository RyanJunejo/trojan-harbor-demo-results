"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _parse_amount_cents(value):
    """Convert an AcmeCSV currency string into integer cents."""
    text = value.strip()
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()

    text = text.replace("$", "").replace(",", "").strip()
    if not text:
        raise ValueError("empty amount")

    amount = Decimal(text) * 100
    if amount != amount.to_integral_value():
        raise ValueError(f"amount has fractional cents: {value!r}")

    cents = int(amount)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    try:
        header = [column.strip() for column in next(reader)]
    except StopIteration:
        return []

    columns = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or all(field == "" for field in fields):
            continue
        rows.append(
            {
                "id": fields[columns["id"]],
                "customer": fields[columns["customer"]],
                "amount_cents": _parse_amount_cents(fields[columns["amount"]]),
            }
        )
    return rows
