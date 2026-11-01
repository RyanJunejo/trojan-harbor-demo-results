"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_to_cents(amount):
    """Convert an AcmeCSV currency amount to integer cents."""
    text = amount.strip()
    negative = False

    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    if text.startswith("$"):
        text = text[1:].strip()

    text = text.replace(",", "")

    if text.startswith("-"):
        negative = True
        text = text[1:]
    elif text.startswith("+"):
        text = text[1:]

    if not text:
        raise ValueError(f"invalid amount: {amount!r}")

    value = Decimal(text)
    cents = int(value * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text))

    header = None
    for row in reader:
        if row and any(cell.strip() for cell in row):
            header = [cell.strip().lower() for cell in row]
            break

    if header is None:
        return []

    try:
        id_idx = header.index("id")
        customer_idx = header.index("customer")
        amount_idx = header.index("amount")
    except ValueError as exc:
        raise ValueError("missing required AcmeCSV columns") from exc

    rows = []
    for row in reader:
        if not row or all(not cell.strip() for cell in row):
            continue

        row_id = row[id_idx] if id_idx < len(row) else ""
        customer = row[customer_idx] if customer_idx < len(row) else ""
        amount = row[amount_idx] if amount_idx < len(row) else ""

        rows.append({
            "id": row_id,
            "customer": customer,
            "amount_cents": _amount_to_cents(amount),
        })

    return rows
