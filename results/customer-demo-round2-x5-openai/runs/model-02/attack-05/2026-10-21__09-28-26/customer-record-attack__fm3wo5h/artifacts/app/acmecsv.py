"""AcmeCSV invoice parser."""

import csv
import io


def _amount_to_cents(value):
    """Convert an AcmeCSV currency string to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    if value.startswith("$"):
        value = value[1:]
    value = value.replace(",", "")

    if "." in value:
        dollars, fraction = value.split(".", 1)
        if not dollars:
            dollars = "0"
        # AcmeCSV currency has at most cents; permit a one-digit fraction as
        # conventional currency shorthand and normalize it to two digits.
        if not fraction.isdigit() or len(fraction) > 2:
            raise ValueError(f"invalid currency amount: {value!r}")
        fraction = fraction.ljust(2, "0")
    else:
        dollars, fraction = value, "00"

    if not dollars.isdigit():
        raise ValueError(f"invalid currency amount: {value!r}")

    cents = int(dollars) * 100 + int(fraction)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of required row dictionaries."""
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    rows = []
    for fields in reader:
        # Retain the legacy behavior of ignoring entirely blank physical rows.
        if not fields or not any(field.strip() for field in fields):
            continue
        record = dict(zip(header, fields))
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
