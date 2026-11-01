"""AcmeCSV invoice parser."""


def _parse_csv(text):
    """Parse CSV text honoring RFC-style quoting (commas, newlines, doubled quotes)."""
    rows = []
    row = []
    field = []
    i = 0
    n = len(text)
    in_quotes = False
    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')
                    i += 1
                else:
                    in_quotes = False
            else:
                field.append(ch)
        else:
            if ch == '"':
                in_quotes = True
            elif ch == ',':
                row.append(''.join(field))
                field = []
            elif ch == '\n':
                row.append(''.join(field))
                field = []
                if row != ['']:
                    rows.append(row)
                row = []
            elif ch == '\r':
                pass
            else:
                field.append(ch)
        i += 1
    if in_quotes:
        row.append(''.join(field))
        rows.append(row)
    elif field or row:
        row.append(''.join(field))
        if row != ['']:
            rows.append(row)
    return rows


def _amount_to_cents(amount):
    """Convert a currency string to integer cents."""
    s = amount.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1]
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '').strip()
    if not s:
        return 0
    if '.' in s:
        dollars, cents = s.split('.', 1)
        cents = (cents + '00')[:2]
        value = int(dollars or '0') * 100 + int(cents)
    else:
        value = int(s) * 100
    return -value if negative else value


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    rows = _parse_csv(text)
    if not rows:
        return []
    header = rows[0]
    results = []
    for raw in rows[1:]:
        record = dict(zip(header, raw))
        results.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return results
