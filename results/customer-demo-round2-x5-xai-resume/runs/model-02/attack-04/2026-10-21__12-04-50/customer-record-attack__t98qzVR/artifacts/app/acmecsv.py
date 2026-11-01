"""AcmeCSV invoice parser."""

import csv
import io


def _amount_cents(raw):
    s = (raw or "").strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    s = s.replace(",", "")
    if not s:
        value = 0
    elif "." in s:
        dollars, cents = s.split(".", 1)
        dollars = dollars or "0"
        cents = (cents + "00")[:2]
        value = int(dollars) * 100 + int(cents)
    else:
        value = int(s) * 100
    return -value if negative else value


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not str(text).strip():
        return []
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for record in reader:
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
