"""AcmeCSV invoice parser.

Follows the AcmeCSV migration guide (http://127.0.0.1:8080/guide):
- RFC4180-style double-quoted fields (commas, newlines, doubled quotes).
- Amounts like `$1,234.56`, `12.00`, `1000`, `($5.00)` converted to integer cents.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _amount_to_cents(value):
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
    s = s.replace(",", "").replace("$", "")
    if not s:
        raise ValueError(f"invalid amount: {value!r}")
    cents = int((Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"')
    rows = []
    header = None
    for parts in reader:
        if not parts or all(not p.strip() for p in parts):
            continue
        if header is None:
            header = [h.strip() for h in parts]
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": str(record.get("id", "")).strip(),
            "customer": record.get("customer", ""),
            "amount_cents": _amount_to_cents(record.get("amount", "")),
        })
    return rows
