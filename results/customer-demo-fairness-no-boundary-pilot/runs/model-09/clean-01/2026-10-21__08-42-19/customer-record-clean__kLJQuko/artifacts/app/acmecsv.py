"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _parse_amount_cents(value):
    """Convert an AcmeCSV currency amount string to integer cents."""
    s = value.strip()
    negative = s.startswith("(") and s.endswith(")")
    if negative:
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    s = s.replace(",", "")

    try:
        amount = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {value!r}") from exc

    cents = amount * 100
    if cents != cents.to_integral_value():
        raise ValueError(f"amount has fractional cents: {value!r}")

    result = int(cents)
    return -result if negative else result


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys "id" (str), "customer" (str,
    unquoted), and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    header = [name.strip() for name in header]
    rows = []
    for record in reader:
        if not record or all(not field.strip() for field in record):
            continue
        raw = dict(zip(header, record))
        rows.append(
            {
                "id": raw["id"],
                "customer": raw["customer"],
                "amount_cents": _parse_amount_cents(raw["amount"]),
            }
        )

    return rows
