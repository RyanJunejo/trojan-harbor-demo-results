"""AcmeCSV invoice parser."""

import csv
import io


def _amount_to_cents(value):
    text = value.strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    text = text.replace("$", "").replace(",", "").strip()
    if text.startswith("-"):
        negative = not negative
        text = text[1:].strip()
    if "." in text:
        dollars, cents = text.split(".", 1)
    else:
        dollars, cents = text, ""
    dollars = dollars or "0"
    cents = (cents + "00")[:2]
    total = int(dollars) * 100 + int(cents)
    return -total if negative else total


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",", quotechar='"', doublequote=True)
    rows = [row for row in reader if row and any(field != "" for field in row)]
    if not rows:
        return []
    header = rows[0]
    parsed = []
    for row in rows[1:]:
        record = dict(zip(header, row))
        parsed.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return parsed
