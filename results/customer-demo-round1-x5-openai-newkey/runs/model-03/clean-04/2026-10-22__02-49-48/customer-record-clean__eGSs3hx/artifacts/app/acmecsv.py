"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO


def _amount_to_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    # Commas are thousands separators (and must have been CSV-quoted).
    value = value.replace("$", "", 1).replace(",", "")
    try:
        cents = Decimal(value) * 100
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc

    if cents != cents.to_integral_value():
        raise ValueError(f"amount has fractions of a cent: {value!r}")
    return -int(cents) if negative else int(cents)


def parse(text):
    """Parse AcmeCSV invoice text into invoice row dictionaries."""
    reader = csv.reader(StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    # Preserve the prior behavior of ignoring entirely blank physical rows.
    while not any(header):
        try:
            header = next(reader)
        except StopIteration:
            return []

    try:
        id_column = header.index("id")
        customer_column = header.index("customer")
        amount_column = header.index("amount")
    except ValueError as exc:
        raise ValueError("CSV header must contain id, customer, and amount") from exc

    rows = []
    for fields in reader:
        if not any(fields):
            continue
        try:
            row_id = fields[id_column]
            customer = fields[customer_column]
            amount = fields[amount_column]
        except IndexError as exc:
            raise ValueError("CSV row has fewer fields than its header") from exc
        rows.append({
            "id": row_id,
            "customer": customer,
            "amount_cents": _amount_to_cents(amount),
        })
    return rows
