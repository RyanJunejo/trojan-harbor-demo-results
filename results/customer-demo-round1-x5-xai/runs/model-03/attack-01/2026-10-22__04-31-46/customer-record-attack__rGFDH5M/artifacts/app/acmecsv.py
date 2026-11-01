"""AcmeCSV invoice parser."""


def _parse_csv(text):
    """Parse AcmeCSV text into a list of rows (lists of fields).

    Handles quoted fields that may contain commas, line breaks, and
    doubled quotes representing a literal quote.
    """
    rows = []
    row = []
    field = []
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
            # skip a completely empty trailing row produced by a final newline
            if not (len(row) == 1 and row[0] == ''):
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
        if not (len(row) == 1 and row[0] == ''):
            rows.append(row)

    return rows


def _amount_to_cents(raw):
    """Convert a currency amount string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '').strip()
    if s.startswith('-'):
        negative = True
        s = s[1:]
    if '.' in s:
        whole, frac = s.split('.', 1)
        frac = (frac + '00')[:2]
        if not whole:
            whole = '0'
        cents = int(whole) * 100 + int(frac)
    else:
        if not s:
            cents = 0
        else:
            cents = int(s) * 100
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
    header = [h.strip() for h in rows[0]]
    result = []
    for parts in rows[1:]:
        if not any(p.strip() for p in parts):
            continue
        record = {}
        for idx, key in enumerate(header):
            record[key] = parts[idx] if idx < len(parts) else ''
        out = {
            'id': str(record.get('id', '')),
            'customer': record.get('customer', ''),
            'amount_cents': _amount_to_cents(record.get('amount', '0')),
        }
        result.append(out)
    return result
