"""AcmeCSV invoice parser."""


def _parse_csv_line(line):
    """Split a CSV line honoring double-quoted fields and escaped quotes."""
    fields = []
    current = []
    in_quotes = False
    i = 0
    while i < len(line):
        ch = line[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < len(line) and line[i + 1] == '"':
                    current.append('"')
                    i += 1
                else:
                    in_quotes = False
            else:
                current.append(ch)
        else:
            if ch == '"':
                in_quotes = True
            elif ch == ',':
                fields.append(''.join(current))
                current = []
            else:
                current.append(ch)
        i += 1
    fields.append(''.join(current))
    return fields


def _parse_rows(text):
    """Parse CSV text into rows, allowing quoted newlines."""
    rows = []
    current = []
    in_quotes = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if in_quotes:
            current.append(ch)
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    current.append(text[i + 1])
                    i += 1
                else:
                    in_quotes = False
        else:
            if ch == '"':
                in_quotes = True
                current.append(ch)
            elif ch == '\n':
                line = ''.join(current).rstrip('\r')
                if line.strip():
                    rows.append(_parse_csv_line(line))
                current = []
            else:
                current.append(ch)
        i += 1
    if current:
        line = ''.join(current).rstrip('\r')
        if line.strip():
            rows.append(_parse_csv_line(line))
    return rows


def _amount_to_cents(raw):
    value = raw.strip()
    negative = False
    if value.startswith('(') and value.endswith(')'):
        negative = True
        value = value[1:-1]
    if value.startswith('$'):
        value = value[1:]
    value = value.replace(',', '').strip()
    if not value:
        cents = 0
    elif '.' in value:
        dollars, frac = value.split('.', 1)
        dollars = dollars or '0'
        frac = (frac + '00')[:2]
        cents = int(dollars) * 100 + int(frac)
    else:
        cents = int(value) * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    rows = _parse_rows(text)
    if not rows:
        return []
    header = rows[0]
    try:
        id_idx = header.index('id')
        customer_idx = header.index('customer')
        amount_idx = header.index('amount')
    except ValueError:
        id_idx, customer_idx, amount_idx = 0, 1, 2
    result = []
    for parts in rows[1:]:
        while len(parts) <= max(id_idx, customer_idx, amount_idx):
            parts.append('')
        result.append({
            'id': parts[id_idx],
            'customer': parts[customer_idx],
            'amount_cents': _amount_to_cents(parts[amount_idx]),
        })
    return result
