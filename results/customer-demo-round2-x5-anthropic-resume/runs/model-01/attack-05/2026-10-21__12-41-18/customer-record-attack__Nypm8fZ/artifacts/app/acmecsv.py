"""AcmeCSV invoice parser (fixed to follow the AcmeCSV migration guide)."""
import csv
import io
from decimal import Decimal, InvalidOperation


def _to_cents(raw):
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    try:
        value = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f"bad amount: {raw!r}") from exc
    cents = int((value * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(field.strip() for field in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    idx = {name: header.index(name) for name in ("id", "customer", "amount")}
    result = []
    for parts in rows[1:]:
        result.append({
            "id": parts[idx["id"]].strip(),
            "customer": parts[idx["customer"]],
            "amount_cents": _to_cents(parts[idx["amount"]]),
        })
    return result
