"""AcmeCSV invoice parser.

Parses the AcmeCSV invoice dialect defined by the migration guide.
"""


def _parse_csv(text):
    """Parse AcmeCSV text into a list of rows (lists of field strings).

    Supports quoted fields that may contain commas and line breaks, and
    doubled quotes inside quoted fields.
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
                # Doubled quote -> literal quote; otherwise end of quoted field
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
            # Skip a trailing empty row produced by a final newline
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

    # Flush last field/row if the text did not end with a newline
    if field or row:
        row.append(''.join(field))
        if not (len(row) == 1 and row[0] == ''):
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
            whole = whole + '0' if whole == '-' else '0'
        # Keep only the first two fractional digits as cents; ignore further
        # digits if present (amounts in the dialect use two places).
        frac = (frac + '00')[:2]
        sign = -1 if whole.startswith('-') else 1
        whole_digits = whole[1:] if whole.startswith('-') else whole
        cents = sign * (int(whole_digits) * 100 + int(frac))
    else:
        cents = int(s) * 100
    if negative:
        cents = -abs(cents)
    return cents


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
    header = rows[0]
    # Map header names to indices; require the known columns.
    try:
        id_i = header.index('id')
        cust_i = header.index('customer')
        amt_i = header.index('amount')
    except ValueError:
        # Fall back to positional columns if header names differ.
        id_i, cust_i, amt_i = 0, 1, 2

    result = []
    for parts in rows[1:]:
        # Skip fully empty rows
        if not any(p.strip() for p in parts):
            continue
        # Pad short rows so indexing is safe
        while len(parts) <= max(id_i, cust_i, amt_i):
            parts.append('')
        result.append({
            'id': parts[id_i],
            'customer': parts[cust_i],
            'amount_cents': _amount_to_cents(parts[amt_i]),
        })
    return result
