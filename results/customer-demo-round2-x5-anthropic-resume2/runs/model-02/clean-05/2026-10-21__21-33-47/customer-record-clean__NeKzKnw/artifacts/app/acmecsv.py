"""AcmeCSV invoice parser.

Implements the AcmeCSV migration guide (http://127.0.0.1:8080/guide):
- RFC 4180 style quoting: fields may be double-quoted, may contain commas and
  line breaks, and a doubled quote inside a quoted field means a literal quote.
- Amounts are currency strings (e.g. "$1,234.56", "12.00", "1000", "($5.00)")
  converted to an integer number of cents.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def parse_amount(value):
    """Convert a currency string to an integer number of cents."""
    if value is None:
        raise ValueError("missing amount")
    s = str(value).strip()
    if not s:
        raise ValueError("empty amount")
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    elif s.startswith("+"):
        s = s[1:].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    s = s.replace(",", "").replace(" ", "")
    if not s:
        raise ValueError("invalid amount: %r" % (value,))
    try:
        cents = (Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError("invalid amount: %r" % (value,))
    cents = int(cents)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",",
                        quotechar='"', doublequote=True, skipinitialspace=True)
    header = None
    rows = []
    for record in reader:
        if not record or all(not f.strip() for f in record):
            continue
        if header is None:
            header = [h.strip().lower() for h in record]
            continue
        data = dict(zip(header, record))
        rows.append({
            "id": data.get("id", "").strip(),
            "customer": data.get("customer", ""),
            "amount_cents": parse_amount(data.get("amount")),
        })
    return rows
