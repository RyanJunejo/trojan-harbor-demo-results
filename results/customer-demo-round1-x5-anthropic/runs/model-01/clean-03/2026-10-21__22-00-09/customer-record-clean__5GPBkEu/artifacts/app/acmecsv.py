"""AcmeCSV invoice parser.

Follows the AcmeCSV migration guide (served at http://127.0.0.1:8080/guide):

- Fields are comma-separated; any field may be double-quoted and may then
  contain commas and line breaks. A doubled quote inside a quoted field is a
  literal quote.
- Amounts are currency strings like ``$1,234.56``, ``12.00`` or ``1000``.
  A value wrapped in parentheses is negative.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def parse_amount(value):
    """Convert a currency string to an integer number of cents."""
    s = str(value).strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    s = s.replace(",", "")
    if not s:
        raise ValueError(f"invalid amount: {value!r}")
    cents = (Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    cents = int(cents)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not text.strip():
        return []
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"',
                        doublequote=True, skipinitialspace=False)
    header = None
    rows = []
    for parts in reader:
        if not parts or all(p.strip() == "" for p in parts):
            continue
        if header is None:
            header = [h.strip() for h in parts]
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": str(record.get("id", "")).strip(),
            "customer": record.get("customer", ""),
            "amount_cents": parse_amount(record.get("amount", "")),
        })
    return rows
