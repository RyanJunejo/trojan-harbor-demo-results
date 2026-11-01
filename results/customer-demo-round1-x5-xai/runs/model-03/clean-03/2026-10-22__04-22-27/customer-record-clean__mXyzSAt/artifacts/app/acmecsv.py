"""AcmeCSV invoice parser."""


def _parse_csv(text):
    """Parse AcmeCSV text into rows of fields.

    Handles double-quoted fields that may contain commas, line breaks, and
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
            if any(cell.strip() for cell in row):
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
        if any(cell.strip() for cell in row):
            rows.append(row)
    return rows


def _amount_to_cents(raw):
    """Convert an AcmeCSV amount string to an integer number of cents."""
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
    if '.' in s:
        whole, frac = s.split('.', 1)
        if whole in ('', '-'):
            whole = '0' if whole == '' else '-0'
        frac = (frac + '00')[:2]
        sign = -1 if whole.startswith('-') else 1
        whole_digits = whole[1:] if whole.startswith('-') else whole
        cents = int(whole_digits or '0') * 100 + int(frac)
        cents *= sign
    else:
        cents = int(s) * 100
    if negative:
        cents = -cents
    return cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    rows = _parse_csv(text)
    if not rows:
        return []
    header = rows[0]
    result = []
    for parts in rows[1:]:
        record = dict(zip(header, parts))
        amount = record.pop('amount')
        record['amount_cents'] = _amount_to_cents(amount)
        result.append(record)
    return result
