"""AcmeCSV invoice parser, following the AcmeCSV migration guide."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _parse_amount(raw):
    """Convert an AcmeCSV currency string such as $1,234.56 to integer cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    try:
        value = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {raw!r}") from exc
    cents = int((value * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows_iter = (row for row in reader if any(field.strip() for field in row))
    try:
        header = [h.strip() for h in next(rows_iter)]
    except StopIteration:
        return []
    rows = []
    for fields in rows_iter:
        record = dict(zip(header, fields))
        rows.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _parse_amount(record["amount"]),
        })
    return rows
