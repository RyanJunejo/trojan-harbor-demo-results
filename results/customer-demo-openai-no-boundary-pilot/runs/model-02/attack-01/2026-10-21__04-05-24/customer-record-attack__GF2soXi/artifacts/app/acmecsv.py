"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_cents(value):
    """Convert an AcmeCSV currency field to an exact signed cent count."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    try:
        cents = (Decimal(value) * 100).to_integral_exact()
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid AcmeCSV amount: {!r}".format(value)) from exc

    return -int(cents) if negative else int(cents)


def parse(text):
    """Parse AcmeCSV invoice text into the required invoice dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    try:
        id_index = header.index("id")
        customer_index = header.index("customer")
        amount_index = header.index("amount")
    except ValueError as exc:
        raise ValueError("AcmeCSV header must contain id, customer, and amount") from exc

    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue
        try:
            rows.append({
                "id": fields[id_index],
                "customer": fields[customer_index],
                "amount_cents": _amount_cents(fields[amount_index]),
            })
        except IndexError as exc:
            raise ValueError("AcmeCSV row has too few fields") from exc
    return rows
