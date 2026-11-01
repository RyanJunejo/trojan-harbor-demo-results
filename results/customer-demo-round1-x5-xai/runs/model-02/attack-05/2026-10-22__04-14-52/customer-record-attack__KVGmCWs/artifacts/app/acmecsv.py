"""AcmeCSV invoice parser."""

import csv
import io


def _amount_cents(raw):
    """Convert an AcmeCSV currency string to integer cents."""
    amount = raw.strip()
    negative = False
    if amount.startswith("(") and amount.endswith(")"):
        negative = True
        amount = amount[1:-1].strip()
    if amount.startswith("$"):
        amount = amount[1:].strip()
    amount = amount.replace(",", "")
    if "." in amount:
        dollars, frac = amount.split(".", 1)
        frac = (frac + "00")[:2]
        value = int(dollars or "0") * 100 + int(frac or "0")
    else:
        value = int(amount or "0") * 100
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
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _amount_cents(record["amount"]),
            }
        )
    return rows
