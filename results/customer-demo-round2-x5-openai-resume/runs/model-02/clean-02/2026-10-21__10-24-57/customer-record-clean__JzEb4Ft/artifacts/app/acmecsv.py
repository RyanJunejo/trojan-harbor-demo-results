"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def parse(text):
    """Parse AcmeCSV invoice text into rows with IDs, customers, and cents."""
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
        invoice_id = fields[columns["id"]]
        customer = fields[columns["customer"]]
        amount_text = fields[columns["amount"]].strip()

        negative = amount_text.startswith("(") and amount_text.endswith(")")
        if negative:
            amount_text = amount_text[1:-1].strip()
        amount_text = amount_text.replace("$", "").replace(",", "").strip()
        cents = int(Decimal(amount_text) * 100)
        if negative:
            cents = -cents

        rows.append({"id": invoice_id, "customer": customer, "amount_cents": cents})
    return rows
