"""AcmeCSV invoice parser following the AcmeCSV migration guide."""
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
    if not s:
        raise ValueError("empty amount")
    cents = int((Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", quotechar='"', doublequote=True)
    rows_iter = (r for r in reader if r and any(f.strip() for f in r))
    header = next(rows_iter, None)
    if header is None:
        return []
    header = [h.strip() for h in header]
    idx = {name: header.index(name) for name in ("id", "customer", "amount")}
    rows = []
    for r in rows_iter:
        rows.append({
            "id": r[idx["id"]],
            "customer": r[idx["customer"]],
            "amount_cents": _amount_to_cents(r[idx["amount"]]),
        })
    return rows
