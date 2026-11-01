"""AcmeCSV invoice parser."""

import csv
import io


def _parse_amount_cents(value):
    """Convert an AcmeCSV currency amount to integer cents."""
    text = value.strip()
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()

    text = text.replace("$", "").replace(",", "").strip()

    if text.startswith("-"):
        negative = True
        text = text[1:].strip()

    if "." in text:
        dollars, cents = text.split(".", 1)
        dollars = dollars or "0"
        cents = cents or "0"
        if len(cents) == 1:
            cents += "0"
        elif len(cents) > 2:
            raise ValueError(f"invalid amount: {value!r}")
        total = int(dollars) * 100 + int(cents)
    else:
        total = int(text) * 100

    return -total if negative else total


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys: "id" (str), "customer" (str),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))

    header = None
    for row in reader:
        if row and any(cell.strip() for cell in row):
            header = [cell.strip() for cell in row]
            break

    if header is None:
        return []

    positions = {name: i for i, name in enumerate(header)}
    required = ("id", "customer", "amount")
    if not all(name in positions for name in required):
        missing = [name for name in required if name not in positions]
        raise ValueError(f"missing required column(s): {', '.join(missing)}")

    rows = []
    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        if len(row) != len(header):
            raise ValueError(f"expected {len(header)} fields, got {len(row)}")

        record = {
            "id": row[positions["id"]],
            "customer": row[positions["customer"]],
            "amount_cents": _parse_amount_cents(row[positions["amount"]]),
        }
        rows.append(record)

    return rows
