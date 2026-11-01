"""AcmeCSV invoice parser following the AcmeCSV migration guide."""
import csv
import io
from decimal import Decimal


def _to_cents(raw):
    s = (raw or "").strip()
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
    cents = int((Decimal(s) * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of dicts with keys
    id (str), customer (str, unquoted), amount_cents (int)."""
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", quotechar='"', doublequote=True)
    rows = [r for r in reader if r and any(f.strip() for f in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    idx = {name: header.index(name) for name in ("id", "customer", "amount")}
    result = []
    for r in rows[1:]:
        result.append({
            "id": r[idx["id"]].strip(),
            "customer": r[idx["customer"]],
            "amount_cents": _to_cents(r[idx["amount"]]),
        })
    return result
