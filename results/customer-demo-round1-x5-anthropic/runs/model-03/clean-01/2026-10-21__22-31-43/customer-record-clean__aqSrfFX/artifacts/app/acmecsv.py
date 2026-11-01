"""AcmeCSV invoice parser."""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _amount_to_cents(raw):
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
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", quotechar='"')
    rows = [r for r in reader if r and any(f.strip() for f in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    out = []
    for r in rows[1:]:
        rec = dict(zip(header, r))
        out.append({
            "id": rec["id"].strip(),
            "customer": rec["customer"],
            "amount_cents": _amount_to_cents(rec["amount"]),
        })
    return out
