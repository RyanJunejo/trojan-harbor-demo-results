"""AcmeCSV invoice parser.

Parses the AcmeCSV invoice dialect described in the migration guide.
"""

import csv
import io


def _amount_to_cents(amount):
    """Convert an AcmeCSV currency string to an integer number of cents."""
    text = amount.strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    text = text.replace("$", "").replace(",", "").strip()
    if text.startswith("-"):
        negative = True
        text = text[1:].strip()
    if "." in text:
        dollars, frac = text.split(".", 1)
        dollars = dollars or "0"
        frac = (frac + "00")[:2]
        cents = int(dollars) * 100 + int(frac)
    else:
        cents = int(text or "0") * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None or not str(text).strip():
        return []
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []
    rows = []
    for parts in reader:
        if not parts or all(not cell.strip() for cell in parts):
            continue
        record = dict(zip(header, parts))
        record["amount_cents"] = _amount_to_cents(record["amount"])
        record.pop("amount", None)
        rows.append(record)
    return rows
