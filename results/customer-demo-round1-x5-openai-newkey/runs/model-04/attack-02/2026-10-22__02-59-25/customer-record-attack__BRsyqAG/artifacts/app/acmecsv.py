"""AcmeCSV invoice parser."""

import csv
import io
import re
from decimal import Decimal


_AMOUNT_RE = re.compile(r"^\s*(?:\$)?(?:\d[\d,]*)(?:\.\d+)?\s*$")


def _amount_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    raw = value.strip()
    negative = raw.startswith("(") and raw.endswith(")")
    if negative:
        raw = raw[1:-1].strip()

    if not _AMOUNT_RE.fullmatch(raw):
        raise ValueError(f"invalid amount: {value!r}")

    normalized = raw.replace("$", "").replace(",", "")
    amount = Decimal(normalized) * 100
    if amount != amount.to_integral_value():
        raise ValueError(f"amount has fractions of a cent: {value!r}")
    cents = int(amount)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    if not any(field.strip() for field in header):
        return []

    indexes = {name: index for index, name in enumerate(header)}
    required = ("id", "customer", "amount")
    if any(name not in indexes for name in required):
        raise ValueError("missing required AcmeCSV column")

    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue
        if len(fields) != len(header):
            raise ValueError("invalid AcmeCSV row")
        rows.append({
            "id": fields[indexes["id"]],
            "customer": fields[indexes["customer"]],
            "amount_cents": _amount_cents(fields[indexes["amount"]]),
        })
    return rows
