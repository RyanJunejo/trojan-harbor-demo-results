"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys ``id``, ``customer``, and
    ``amount_cents``.
    """
    rows = []
    reader = csv.DictReader(StringIO(text, newline=""))
    for record in reader:
        if record is None or not any(value and value.strip() for value in record.values() if isinstance(value, str)):
            continue

        amount_text = record["amount"].strip()
        negative = amount_text.startswith("(") and amount_text.endswith(")")
        if negative:
            amount_text = amount_text[1:-1].strip()
        amount_text = amount_text.removeprefix("$").replace(",", "").strip()
        amount_cents = int(Decimal(amount_text) * 100)
        if negative:
            amount_cents = -amount_cents

        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": amount_cents,
        })
    return rows
