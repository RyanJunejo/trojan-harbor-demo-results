"""AcmeCSV invoice parser (per the AcmeCSV migration guide)."""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def _parse_cents(raw):
    s = raw.strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        neg = not neg
        s = s[1:].strip()
    try:
        value = Decimal(s) * 100
    except InvalidOperation as exc:
        raise ValueError(f"bad amount: {raw!r}") from exc
    cents = int(value.to_integral_value(rounding=ROUND_HALF_UP))
    return -cents if neg else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows_iter = (row for row in reader if any(field.strip() for field in row))
    try:
        header = [h.strip() for h in next(rows_iter)]
    except StopIteration:
        return []
    rows = []
    for values in rows_iter:
        record = dict(zip(header, values))
        rows.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _parse_cents(record["amount"]),
        })
    return rows
