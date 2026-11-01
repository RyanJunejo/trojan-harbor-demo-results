"""AcmeCSV invoice parser (follows the AcmeCSV migration guide)."""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _to_cents(raw):
    s = (raw or "").strip()
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
    s = s.replace(",", "")
    cents = int((Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: id (str), customer (str, unquoted),
    and amount_cents (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""))
    header = None
    rows = []
    for parts in reader:
        if not parts or all(not p.strip() for p in parts):
            continue
        if header is None:
            header = [h.strip() for h in parts]
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _to_cents(record["amount"]),
        })
    return rows
