"""AcmeCSV invoice parser."""

import csv
import io


def _parse_amount_cents(amount):
    """Convert a currency string to an integer number of cents."""
    value = amount.strip()
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
        cents = int(dollars or "0") * 100 + int(frac or "0")
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
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return []
    header = rows[0]
    parsed = []
    for row in rows[1:]:
        record = dict(zip(header, row))
        parsed.append(
            {
                "id": str(record["id"]),
                "customer": record["customer"],
                "amount_cents": _parse_amount_cents(record["amount"]),
            }
        )
    return parsed
