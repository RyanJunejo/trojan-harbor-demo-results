"""AcmeCSV invoice parser following the AcmeCSV migration guide."""
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
    s = s.replace(",", "")
    cents = int((Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of dicts with keys
    "id" (str), "customer" (str, unquoted), "amount_cents" (int)."""
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = []
    header = None
    for fields in reader:
        if not fields or all(not f.strip() for f in fields):
            continue
        if header is None:
            header = [h.strip() for h in fields]
            continue
        rec = dict(zip(header, fields))
        rows.append({
            "id": rec["id"].strip(),
            "customer": rec["customer"],
            "amount_cents": _to_cents(rec["amount"]),
        })
    return rows
