"""AcmeCSV invoice parser (follows the AcmeCSV migration guide)."""

import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _parse_amount(value):
    s = value.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    s = s.replace(",", "").replace("_", "").replace(" ", "")
    if not s:
        raise ValueError("empty amount: %r" % value)
    cents = int((Decimal(s) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""))
    header = None
    rows = []
    for fields in reader:
        if not fields or all(not f.strip() for f in fields):
            continue
        if header is None:
            header = [h.strip().lower() for h in fields]
            continue
        rec = dict(zip(header, fields))
        rows.append({
            "id": rec.get("id", fields[0]).strip(),
            "customer": rec.get("customer", fields[1] if len(fields) > 1 else ""),
            "amount_cents": _parse_amount(rec.get("amount", fields[2] if len(fields) > 2 else "")),
        })
    return rows
