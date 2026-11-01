"""AcmeCSV invoice parser, implemented per the AcmeCSV migration guide."""

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_to_cents(raw):
    """Convert a currency string such as '$1,234.56' or '($5.00)' to integer cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = True
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
    rows = [r for r in csv.reader(io.StringIO(text)) if any(f.strip() for f in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    result = []
    for fields in rows[1:]:
        record = dict(zip(header, fields))
        result.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return result
