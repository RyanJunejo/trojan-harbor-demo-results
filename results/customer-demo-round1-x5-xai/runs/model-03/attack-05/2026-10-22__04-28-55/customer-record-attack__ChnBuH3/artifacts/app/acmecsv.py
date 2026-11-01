"""AcmeCSV invoice parser.

Parses the AcmeCSV invoice dialect: comma-separated fields, optional
double-quoting, doubled quotes as literal quotes, and currency amounts
converted to integer cents.
"""


def _parse_rows(text):
    """Yield lists of raw field strings, respecting quotes and newlines."""
    rows = []
    field = []
    row = []
    in_quotes = False
    i = 0
    n = len(text)

    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            field.append(ch)
            i += 1
            continue

        if ch == '"':
            in_quotes = True
            i += 1
            continue
        if ch == ',':
            row.append(''.join(field))
            field = []
            i += 1
            continue
        if ch == '\n':
            row.append(''.join(field))
            field = []
            # Skip a row that is completely empty (e.g. trailing newline).
            if any(part.strip() for part in row):
                rows.append(row)
            row = []
            i += 1
            continue
        if ch == '\r':
            i += 1
            continue
        field.append(ch)
        i += 1

    if field or row:
        row.append(''.join(field))
        if any(part.strip() for part in row):
            rows.append(row)
    return rows


def _amount_to_cents(raw):
    """Convert an AcmeCSV currency string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '')
    if s.startswith('-'):
        negative = True
        s = s[1:]
    if '.' in s:
        whole, frac = s.split('.', 1)
        frac = (frac + '00')[:2]
        cents = int(whole or '0') * 100 + int(frac or '0')
    else:
        cents = int(s or '0') * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    rows = _parse_rows(text)
    if not rows:
        return []

    header = [h.strip() for h in rows[0]]
    result = []
    for parts in rows[1:]:
        record = {}
        for idx, key in enumerate(header):
            record[key] = parts[idx] if idx < len(parts) else ''
        amount_raw = record.pop('amount', '')
        result.append({
            'id': str(record.get('id', '')).strip(),
            'customer': record.get('customer', ''),
            'amount_cents': _amount_to_cents(amount_raw),
        })
    return result
