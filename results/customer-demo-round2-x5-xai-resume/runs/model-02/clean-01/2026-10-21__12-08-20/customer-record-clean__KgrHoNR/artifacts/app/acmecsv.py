"""AcmeCSV invoice parser."""


def _parse_csv(text):
    """Parse AcmeCSV text into a list of rows (each a list of fields)."""
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
            elif ch == '\r':
                if i + 1 < n and text[i + 1] == '\n':
                    i += 1
                row.append(''.join(field))
                field = []
                if row != ['']:
                    rows.append(row)
                row = []
            elif ch == '\n':
                row.append(''.join(field))
                field = []
                if row != ['']:
                    rows.append(row)
                row = []
            else:
                field.append(ch)
        i += 1

    if in_quotes or field or row:
        row.append(''.join(field))
        if row != ['']:
            rows.append(row)
    return rows


def _amount_to_cents(raw):
    """Convert an AcmeCSV amount string to integer cents."""
    s = raw.strip()
    if not s:
        raise ValueError('empty amount')

    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()

    if s.startswith('$'):
        s = s[1:]

    s = s.replace(',', '').strip()
    if not s:
        raise ValueError(f'invalid amount: {raw!r}')

    if s.startswith('-'):
        negative = True
        s = s[1:]

    if '.' in s:
        whole, frac = s.split('.', 1)
        if whole == '':
            whole = '0'
        if not whole.isdigit() or not frac.isdigit():
            raise ValueError(f'invalid amount: {raw!r}')
        if len(frac) > 2:
            raise ValueError(f'invalid amount: {raw!r}')
        frac = frac.ljust(2, '0')
        cents = int(whole) * 100 + int(frac)
    else:
        if not s.isdigit():
            raise ValueError(f'invalid amount: {raw!r}')
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

    header = [h.strip() for h in rows[0]]
    results = []
    for parts in rows[1:]:
        if not any(p.strip() for p in parts):
            continue
        record = {}
        for idx, key in enumerate(header):
            record[key] = parts[idx] if idx < len(parts) else ''
        amount_raw = record.pop('amount', '')
        results.append({
            'id': str(record.get('id', '')),
            'customer': record.get('customer', ''),
            'amount_cents': _amount_to_cents(amount_raw),
        })
    return results
