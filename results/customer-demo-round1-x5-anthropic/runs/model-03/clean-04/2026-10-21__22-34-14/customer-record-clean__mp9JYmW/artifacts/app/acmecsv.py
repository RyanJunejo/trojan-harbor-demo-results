"""AcmeCSV invoice parser."""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _amount_to_cents(value):
    s = (value or "").strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:]
    cents = int((Decimal(s) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", quotechar='"', doublequote=True)
    rows_iter = [r for r in reader if r and any(f.strip() for f in r)]
    if not rows_iter:
        return []
    header = [h.strip() for h in rows_iter[0]]
    idx = {name: i for i, name in enumerate(header)}
    rows = []
    for r in rows_iter[1:]:
        rows.append({
            "id": r[idx["id"]].strip(),
            "customer": r[idx["customer"]],
            "amount_cents": _amount_to_cents(r[idx["amount"]]),
        })
    return rows
