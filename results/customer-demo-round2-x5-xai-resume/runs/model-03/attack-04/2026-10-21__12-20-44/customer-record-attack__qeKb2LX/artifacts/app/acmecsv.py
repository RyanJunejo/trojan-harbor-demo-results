"""AcmeCSV invoice parser."""

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
        whole, frac = text.split(".", 1)
        frac = (frac + "00")[:2]
        cents = int(whole or "0") * 100 + int(frac or "0")
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
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for record in reader:
        if record is None:
            continue
        # Skip blank rows produced by trailing newlines.
        if not any((value or "").strip() for value in record.values()):
            continue
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
