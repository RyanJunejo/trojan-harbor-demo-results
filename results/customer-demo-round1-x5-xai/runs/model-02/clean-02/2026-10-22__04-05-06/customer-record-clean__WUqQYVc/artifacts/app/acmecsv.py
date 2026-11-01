"""AcmeCSV invoice parser."""

import csv
import io


def _amount_cents(raw):
    value = raw.strip()
    negative = False
    if value.startswith("(") and value.endswith(")"):
        negative = True
        value = value[1:-1].strip()
    value = value.replace("$", "").replace(",", "").strip()
    if not value:
        cents = 0
    elif "." in value:
        dollars, frac = value.split(".", 1)
        frac = (frac + "00")[:2]
        cents = int(dollars or "0") * 100 + int(frac)
    else:
        cents = int(value) * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not text.strip():
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
