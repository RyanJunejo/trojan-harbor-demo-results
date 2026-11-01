"""Parser for AcmeCSV invoice files."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_in_cents(value):
    """Convert an AcmeCSV dollar amount to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    try:
        dollars = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc

    cents = dollars * 100
    if cents != cents.to_integral_value():
        raise ValueError(f"amount has fractional cents: {value!r}")
    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV text into invoice dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))

    header = None
    for row in reader:
        if row and any(field.strip() for field in row):
            header = row
            break
    if header is None:
        return []

    try:
        id_index = header.index("id")
        customer_index = header.index("customer")
        amount_index = header.index("amount")
    except ValueError as exc:
        raise ValueError("AcmeCSV header must contain id, customer, and amount") from exc

    rows = []
    required_index = max(id_index, customer_index, amount_index)
    for row in reader:
        if not row or not any(field.strip() for field in row):
            continue
        if len(row) <= required_index:
            raise ValueError("invoice row has too few fields")
        rows.append({
            "id": row[id_index],
            "customer": row[customer_index],
            "amount_cents": _amount_in_cents(row[amount_index]),
        })
    return rows
