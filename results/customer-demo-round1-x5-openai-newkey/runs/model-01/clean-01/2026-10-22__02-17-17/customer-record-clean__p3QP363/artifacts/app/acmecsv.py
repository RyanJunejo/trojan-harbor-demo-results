"""Parse invoices using the AcmeCSV migration guide's CSV and currency rules."""

import csv
from decimal import Decimal, localcontext
from io import StringIO


def _amount_cents(value):
    """Convert a dollar amount to cents without binary floating-point rounding."""
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    value = value.removeprefix("$").replace(",", "")
    with localcontext() as context:
        context.prec = max(28, len(value) + 2)
        cents = Decimal(value) * 100
        if not cents.is_finite() or cents != cents.to_integral_value():
            raise ValueError("Amount must represent a whole number of cents")
        result = int(cents)
    return -result if negative else result


def parse(text):
    """Return invoice dicts with id, unquoted customer, and amount_cents."""
    # Let csv handle entire records: quoted fields may contain line breaks.
    records = csv.reader(StringIO(text, newline=""))
    header = next((row for row in records if row and any(row)), None)
    if header is None:
        return []

    rows = []
    for fields in records:
        if not fields or (len(fields) == 1 and not fields[0].strip()):
            continue
        record = dict(zip(header, fields))
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_cents(record["amount"]),
        })
    return rows
