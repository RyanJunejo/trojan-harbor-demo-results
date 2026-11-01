"""AcmeCSV invoice parser."""

import csv
import io
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def _amount_to_cents(value):
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()

    value = value.replace("$", "").replace(",", "").strip()
    if not value:
        raise ValueError("empty amount")
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", value):
        raise ValueError(f"invalid amount: {value!r}")

    try:
        cents = (Decimal(value) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc
    return int(-cents if negative else cents)


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text), dialect="excel")
    header = None
    for fields in reader:
        if fields and not all(not field.strip() for field in fields):
            header = fields
            break
    if header is None:
        return []
    header = [field.strip() for field in header]

    try:
        id_index = header.index("id")
        customer_index = header.index("customer")
        amount_index = header.index("amount")
    except ValueError as exc:
        raise ValueError("missing required header") from exc

    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        rows.append({
            "id": fields[id_index],
            "customer": fields[customer_index],
            "amount_cents": _amount_to_cents(fields[amount_index]),
        })
    return rows
