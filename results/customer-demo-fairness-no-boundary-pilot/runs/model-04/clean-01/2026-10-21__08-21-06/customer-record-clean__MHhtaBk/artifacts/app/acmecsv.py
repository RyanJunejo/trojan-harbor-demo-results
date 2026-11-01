"""AcmeCSV invoice parser.

Implements the AcmeCSV dialect described in the migration guide served at
http://127.0.0.1:8080/guide:

* Fields are comma-separated; any field may be double-quoted. Quoted fields may
  contain commas and line breaks, and a doubled quote ("") inside a quoted
  field is a literal quote.
* Amounts are currency strings ("$1,234.56", "12.00", "1000"). The leading
  "$" and thousands separators are removed and the value is returned as an
  integer number of cents. A value wrapped in parentheses is negative.
"""

import csv
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def parse_amount(value):
    """Convert an AcmeCSV currency string into an integer number of cents."""
    if value is None:
        raise ValueError("missing amount")
    s = str(value).strip()
    if not s:
        raise ValueError("empty amount")

    negative = False
    # Parentheses denote a negative value, e.g. "($5.00)".
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    # Explicit sign (before or after the currency symbol).
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
    elif s.startswith("+"):
        s = s[1:].strip()

    # Remove thousands separators.
    s = s.replace(",", "")
    if not s:
        raise ValueError("invalid amount: %r" % (value,))

    try:
        dec = Decimal(s)
    except InvalidOperation:
        raise ValueError("invalid amount: %r" % (value,))

    cents = int((dec * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys: "id" (str), "customer" (str, with CSV
    quoting removed), and "amount_cents" (int).
    """
    if text is None:
        return []
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    # Strip a UTF-8 BOM if present.
    if text.startswith("\ufeff"):
        text = text[1:]

    reader = csv.reader(
        io.StringIO(text, newline=""),
        delimiter=",",
        quotechar='"',
        doublequote=True,
        skipinitialspace=False,
        strict=False,
    )

    header = None
    rows = []
    for record in reader:
        # Skip blank lines.
        if not record or all(not cell.strip() for cell in record):
            continue
        if header is None:
            header = [h.strip().lower() for h in record]
            continue

        fields = dict(zip(header, record))
        row_id = fields.get("id", "")
        customer = fields.get("customer", "")
        amount = fields.get("amount", "")
        rows.append(
            {
                "id": str(row_id).strip(),
                "customer": customer,
                "amount_cents": parse_amount(amount),
            }
        )
    return rows
