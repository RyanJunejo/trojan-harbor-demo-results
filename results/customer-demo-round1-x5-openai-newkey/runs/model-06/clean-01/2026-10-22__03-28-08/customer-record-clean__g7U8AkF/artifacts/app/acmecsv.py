"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    columns = {name: index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields:
            continue

        amount_text = fields[columns["amount"]].strip()
        negative = amount_text.startswith("(") and amount_text.endswith(")")
        if negative:
            amount_text = amount_text[1:-1].strip()
        amount_text = amount_text.replace("$", "").replace(",", "").strip()
        amount_cents = int(Decimal(amount_text) * 100)
        if negative:
            amount_cents = -amount_cents

        rows.append({
            "id": str(fields[columns["id"]]),
            "customer": fields[columns["customer"]],
            "amount_cents": amount_cents,
        })
    return rows
