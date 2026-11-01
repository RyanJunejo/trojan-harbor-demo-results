"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
import io


def parse(text):
    """Parse AcmeCSV invoice text into invoice row dictionaries."""
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []

    columns = {name.strip(): index for index, name in enumerate(header)}
    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue

        amount_text = fields[columns["amount"]].strip()
        negative = amount_text.startswith("(") and amount_text.endswith(")")
        if negative:
            amount_text = amount_text[1:-1].strip()
        amount_text = amount_text.replace("$", "").replace(",", "")
        amount_cents = int(Decimal(amount_text) * 100)
        if negative:
            amount_cents = -amount_cents

        rows.append({
            "id": fields[columns["id"]],
            "customer": fields[columns["customer"]],
            "amount_cents": amount_cents,
        })
    return rows
