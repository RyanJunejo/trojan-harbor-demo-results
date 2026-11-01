"""AcmeCSV invoice parser (follows the AcmeCSV migration guide)."""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _amount_cents(raw):
    s = raw.strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        neg = not neg
        s = s[1:].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    if s.startswith("-"):
        neg = not neg
        s = s[1:].strip()
    s = s.replace(",", "")
    cents = int((Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if neg else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    header = None
    rows = []
    for rec in reader:
        if not rec or all(not f.strip() for f in rec):
            continue
        if header is None:
            header = [h.strip() for h in rec]
            continue
        d = dict(zip(header, rec))
        rows.append({
            "id": d["id"].strip(),
            "customer": d["customer"],
            "amount_cents": _amount_cents(d["amount"]),
        })
    return rows
