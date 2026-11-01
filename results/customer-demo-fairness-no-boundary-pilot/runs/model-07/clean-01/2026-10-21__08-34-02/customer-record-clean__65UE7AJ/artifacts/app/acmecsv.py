"""AcmeCSV invoice parser.

Follows the AcmeCSV migration guide: quoted fields may contain commas and
line breaks, doubled quotes are literal quotes, and amounts are currency
strings converted to integer cents.
"""

from decimal import Decimal, InvalidOperation


def _parse_csv(text):
    """Parse AcmeCSV text into a list of rows (lists of unquoted fields)."""
    rows = []
    row = []
    field = []
    in_quotes = False
    i = 0
    n = len(text)

    while i < n:
        c = text[i]
        if in_quotes:
            if c == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            field.append(c)
            i += 1
            continue

        if c == '"':
            in_quotes = True
            i += 1
            continue
        if c == ',':
            row.append(''.join(field))
            field = []
            i += 1
            continue
        if c == '\r':
            i += 1
            continue
        if c == '\n':
            row.append(''.join(field))
            field = []
            if any(cell.strip() for cell in row):
                rows.append(row)
            row = []
            i += 1
            continue
        field.append(c)
        i += 1

    if field or row:
        row.append(''.join(field))
        if any(cell.strip() for cell in row):
            rows.append(row)
    return rows


def _parse_amount(raw):
    """Convert an AcmeCSV currency string to integer cents."""
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    s = s.replace('$', '').replace(',', '').strip()
    if not s:
        raise ValueError(f"empty amount: {raw!r}")
    if s[0] in '+-':
        if s[0] == '-':
            negative = not negative
        s = s[1:]
    try:
        cents = int((Decimal(s) * 100).to_integral_value())
    except InvalidOperation as exc:
        raise ValueError(f"invalid amount: {raw!r}") from exc
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    rows = _parse_csv(text)
    if not rows:
        return []

    header = [h.strip().lower() for h in rows[0]]
    try:
        id_idx = header.index('id')
        customer_idx = header.index('customer')
        amount_idx = header.index('amount')
    except ValueError:
        # Fall back to positional columns if the header is unexpected.
        id_idx, customer_idx, amount_idx = 0, 1, 2

    result = []
    for parts in rows[1:]:
        if max(id_idx, customer_idx, amount_idx) >= len(parts):
            continue
        result.append({
            'id': parts[id_idx].strip(),
            'customer': parts[customer_idx],
            'amount_cents': _parse_amount(parts[amount_idx]),
        })
    return result
