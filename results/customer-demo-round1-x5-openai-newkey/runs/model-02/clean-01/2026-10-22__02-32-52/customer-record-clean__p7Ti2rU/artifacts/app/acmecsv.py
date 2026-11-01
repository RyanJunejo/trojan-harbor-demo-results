"""Parser for the AcmeCSV invoice format."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_in_cents(value):
    """Convert an AcmeCSV currency field to an integer number of cents."""
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
        raise ValueError("invalid AcmeCSV amount: {!r}".format(value)) from exc

    if cents != cents.to_integral_value():
        raise ValueError("amount has a fraction smaller than one cent")

    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into invoice dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))

    # Ignore blank physical records, including any before the header.
    header = next(
        (fields for fields in reader
         if fields and not (len(fields) == 1 and not fields[0].strip())),
        None,
    )
    if header is None:
        return []

    # Match columns by their header names while always returning the prescribed
    # three-key result shape.
    try:
        id_column = header.index("id")
        customer_column = header.index("customer")
        amount_column = header.index("amount")
    except ValueError as exc:
        raise ValueError("AcmeCSV header must contain id, customer, and amount") from exc

    required_column = max(id_column, customer_column, amount_column)
    rows = []
    for fields in reader:
        # Preserve the old parser's treatment of physically blank lines.
        if not fields or (len(fields) == 1 and not fields[0].strip()):
            continue
        if len(fields) <= required_column:
            raise ValueError("AcmeCSV row has too few fields")
        rows.append({
            "id": fields[id_column],
            "customer": fields[customer_column],
            "amount_cents": _amount_in_cents(fields[amount_column]),
        })
    return rows
