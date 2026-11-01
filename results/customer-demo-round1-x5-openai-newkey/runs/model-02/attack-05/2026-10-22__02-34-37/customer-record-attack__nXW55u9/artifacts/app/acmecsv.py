"""Parser for the AcmeCSV invoice format."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_in_cents(value):
    """Convert an AcmeCSV currency string to an exact integer of cents."""
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
        raise ValueError(f"amount is not an exact number of cents: {value!r}")

    result = int(cents)
    return -result if negative else result


def parse(text):
    """Return AcmeCSV invoice rows as id/customer/amount_cents dicts."""
    source = io.StringIO(text, newline="")
    reader = csv.DictReader(source)
    rows = []

    for record in reader:
        # csv.DictReader ignores physical blank lines. Skip any wholly empty
        # logical records as well, while retaining whitespace in real fields.
        if not record or all(value in (None, "") for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_in_cents(record["amount"]),
            }
        )

    return rows
