"""AcmeCSV invoice parser.

Follows the AcmeCSV migration guide at http://127.0.0.1:8080/guide:
- RFC-4180-style quoting (doubled quotes, embedded commas and newlines).
- Amounts such as $1,234.56, 12.00, 1000, and ($5.00) (negative) become
  integer cents.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _parse_amount(raw):
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    cents = (Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    value = int(cents)
    return -value if negative else value


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows_iter = (row for row in reader if any(field.strip() for field in row))
    try:
        header = [name.strip() for name in next(rows_iter)]
    except StopIteration:
        return []
    rows = []
    for fields in rows_iter:
        record = dict(zip(header, fields))
        rows.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _parse_amount(record["amount"]),
        })
    return rows
