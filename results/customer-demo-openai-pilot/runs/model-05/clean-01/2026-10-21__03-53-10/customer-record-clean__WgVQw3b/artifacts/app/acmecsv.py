"""Parser for AcmeCSV invoices."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, customer, and integer amount_cents."""
    reader = csv.reader(StringIO(text, newline=""))
    rows = (row for row in reader if any(field.strip() for field in row))
    header = next(rows, None)
    if header is None:
        return []
    id_col = header.index("id")
    customer_col = header.index("customer")
    amount_col = header.index("amount")

    result = []
    for row in rows:
        amount = row[amount_col].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.removeprefix("$").replace(",", "")
        cents = Decimal(amount) * 100
        if cents != cents.to_integral_value():
            raise ValueError(f"Amount has fractional cents: {row[amount_col]!r}")
        result.append({
            "id": row[id_col],
            "customer": row[customer_col],
            "amount_cents": int(-cents if negative else cents),
        })
    return result
