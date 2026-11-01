"""AcmeCSV invoice parser."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Parse AcmeCSV invoice text into the required row dictionaries."""
    reader = csv.reader(StringIO(text), skipinitialspace=False)
    rows = [row for row in reader if row and any(field.strip() for field in row)]
    if not rows:
        return []

    header = rows[0]
    id_index = header.index("id")
    customer_index = header.index("customer")
    amount_index = header.index("amount")

    result = []
    for row in rows[1:]:
        amount = row[amount_index].strip()
        negative = amount.startswith("(") and amount.endswith(")")
        if negative:
            amount = amount[1:-1].strip()
        amount = amount.replace("$", "").replace(",", "")
        cents = int(Decimal(amount) * 100)
        if negative:
            cents = -cents
        result.append({
            "id": row[id_index],
            "customer": row[customer_index],
            "amount_cents": cents,
        })
    return result
