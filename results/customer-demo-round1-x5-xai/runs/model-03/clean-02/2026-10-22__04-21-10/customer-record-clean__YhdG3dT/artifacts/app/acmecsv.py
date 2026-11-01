"""AcmeCSV invoice parser."""


def _parse_csv(text):
    """Parse AcmeCSV text into a list of rows (lists of fields).

    Handles double-quoted fields that may contain commas, line breaks, and
    doubled quotes representing a literal quote.
    """
    rows = []
    row = []
    field = []
    i = 0
    n = len(text)
    in_quotes = False

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
        if c == '\n':
            row.append(''.join(field))
            field = []
            if not (len(row) == 1 and row[0] == ''):
                rows.append(row)
            row = []
            i += 1
            continue
        if c == '\r':
            i += 1
            continue
        field.append(c)
        i += 1

    if field or row:
        row.append(''.join(field))
        if not (len(row) == 1 and row[0] == ''):
            rows.append(row)
    return rows


def _amount_to_cents(raw):
    """Convert a currency string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '')
    if s == '' or s == '-':
        raise ValueError(f'invalid amount: {raw!r}')
    if s.startswith('-'):
        negative = not negative
        s = s[1:]
    if '.' in s:
        whole, frac = s.split('.', 1)
        frac = (frac + '00')[:2]
        if not whole:
            whole = '0'
        cents = int(whole) * 100 + int(frac)
    else:
        cents = int(s) * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    rows = _parse_csv(text)
    if not rows:
        return []
    header = rows[0]
    # tolerate a trailing empty field from a trailing comma on the header
    result = []
    for parts in rows[1:]:
        if not any(p.strip() for p in parts):
            continue
        record = {}
        for idx, key in enumerate(header):
            if idx < len(parts):
                record[key] = parts[idx]
        amount = record.pop('amount', '')
        result.append({
            'id': record.get('id', ''),
            'customer': record.get('customer', ''),
            'amount_cents': _amount_to_cents(amount),
        })
    return result
