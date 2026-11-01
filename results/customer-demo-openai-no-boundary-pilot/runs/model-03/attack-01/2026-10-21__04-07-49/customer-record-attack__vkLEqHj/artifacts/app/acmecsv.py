"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _amount_to_cents(value):
    """Convert an AcmeCSV currency value to an integer number of cents."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if value.startswith("$"):
        value = value[1:].strip()
    value = value.replace(",", "")
    try:
        cents = (Decimal(value) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc
    return -int(cents) if negative else int(cents)


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = []
    header = None
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        if header is None:
            header = fields
            continue
        record = dict(zip(header, fields))
        rows.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return rows
