"""Parser for AcmeCSV invoice files."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_in_cents(value):
    """Convert an AcmeCSV currency string to an exact number of cents."""
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
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))

    # Permit empty records around the header while leaving quoted multiline
    # fields entirely in the CSV parser's control.
    header = next((row for row in reader if row), None)
    if header is None:
        return []

    try:
        id_index = header.index("id")
        customer_index = header.index("customer")
        amount_index = header.index("amount")
    except ValueError as exc:
        raise ValueError("AcmeCSV header must contain id, customer, and amount") from exc

    rows = []
    for fields in reader:
        if not fields:
            continue
        try:
            row_id = fields[id_index]
            customer = fields[customer_index]
            amount = fields[amount_index]
        except IndexError as exc:
            raise ValueError("AcmeCSV row has fewer fields than its header") from exc
        rows.append({
            "id": row_id,
            "customer": customer,
            "amount_cents": _amount_in_cents(amount),
        })
    return rows
