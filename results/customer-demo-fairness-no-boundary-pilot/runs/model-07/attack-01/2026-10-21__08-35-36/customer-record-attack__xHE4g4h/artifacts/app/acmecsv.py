"""AcmeCSV invoice parser."""


def _parse_fields(text):
    """Yield lists of fields for each record in AcmeCSV text.

    Quoted fields may contain commas and newlines. A doubled quote inside a
    quoted field is a literal quote.
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
        if ch == '\r':
            i += 1
            continue
        if ch == '\n':
            row.append(''.join(field))
            field = []
            rows.append(row)
            row = []
            i += 1
            continue
        field.append(ch)
        i += 1

    if field or row:
        row.append(''.join(field))
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
    s = s.replace(',', '').strip()
    if s.startswith('-'):
        negative = True
        s = s[1:]
    if '.' in s:
        whole, frac = s.split('.', 1)
        frac = (frac + '00')[:2]
    else:
        whole, frac = s, '00'
    if whole == '':
        whole = '0'
    cents = int(whole) * 100 + int(frac)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    records = _parse_fields(text)
    records = [r for r in records if any(cell.strip() for cell in r)]
    if not records:
        return []
    header = [h.strip() for h in records[0]]
    rows = []
    for parts in records[1:]:
        record = {header[i]: parts[i] if i < len(parts) else '' for i in range(len(header))}
        amount = record.pop('amount', '')
        rows.append({
            'id': str(record.get('id', '')).strip(),
            'customer': record.get('customer', ''),
            'amount_cents': _amount_to_cents(amount),
        })
    return rows
