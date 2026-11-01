"""AcmeCSV invoice parser."""


def _parse_csv_rows(text):
    """Parse AcmeCSV text into rows of fields.

    Supports double-quoted fields, embedded commas and newlines, and
    doubled quotes as a literal quote character.
    """
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
            # Skip a trailing empty row caused by a final newline.
            if any(cell != '' for cell in row):
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
        if any(cell != '' for cell in row):
            rows.append(row)
    return rows


def _amount_to_cents(amount):
    """Convert a currency string to an integer number of cents."""
    s = amount.strip()
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
    rows = _parse_csv_rows(text)
    if not rows:
        return []
    header = rows[0]
    result = []
    for parts in rows[1:]:
        record = dict(zip(header, parts))
        result.append({
            'id': str(record.get('id', '')),
            'customer': record.get('customer', ''),
            'amount_cents': _amount_to_cents(record.get('amount', '0')),
        })
    return result
