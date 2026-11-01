"""AcmeCSV invoice parser.

Parses AcmeCSV invoice text per the migration guide at
http://127.0.0.1:8080/guide.
"""


def _parse_csv_line(line):
    """Parse one CSV record line into fields (handles quotes)."""
    fields = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] == '"':
            # Quoted field
            i += 1
            buf = []
            while i < n:
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"')
                        i += 2
                    else:
                        i += 1  # closing quote
                        break
                else:
                    buf.append(line[i])
                    i += 1
            fields.append(''.join(buf))
            if i < n and line[i] == ',':
                i += 1
        else:
            # Unquoted field
            j = line.find(',', i)
            if j == -1:
                fields.append(line[i:])
                i = n
            else:
                fields.append(line[i:j])
                i = j + 1
    # Trailing comma means empty final field
    if line.endswith(','):
        fields.append('')
    return fields


def _parse_amount_cents(amount):
    """Convert currency string to integer cents."""
    s = amount.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '')
    if not s:
        return 0
    if '.' in s:
        whole, frac = s.split('.', 1)
        frac = (frac + '00')[:2]
        cents = int(whole or '0') * 100 + int(frac)
    else:
        cents = int(s) * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    # Support quoted fields that may contain newlines by scanning the whole text.
    rows_fields = []
    i = 0
    n = len(text)
    # Normalize to handle both \n and \r\n; keep content intact inside quotes.
    while i < n:
        # Skip blank lines outside of records
        if text[i] in '\r\n':
            i += 1
            continue
        fields = []
        while i < n:
            if text[i] == '"':
                i += 1
                buf = []
                while i < n:
                    if text[i] == '"':
                        if i + 1 < n and text[i + 1] == '"':
                            buf.append('"')
                            i += 2
                        else:
                            i += 1
                            break
                    else:
                        buf.append(text[i])
                        i += 1
                fields.append(''.join(buf))
                if i < n and text[i] == ',':
                    i += 1
                    continue
                # End of record (newline) or EOF
                while i < n and text[i] in '\r\n':
                    i += 1
                    break
                break
            else:
                # Unquoted: read until comma or newline
                start = i
                while i < n and text[i] not in ',\r\n':
                    i += 1
                fields.append(text[start:i])
                if i < n and text[i] == ',':
                    i += 1
                    continue
                while i < n and text[i] in '\r\n':
                    i += 1
                    break
                break
        if fields and any(f.strip() for f in fields):
            rows_fields.append(fields)

    if not rows_fields:
        return []

    header = rows_fields[0]
    result = []
    for parts in rows_fields[1:]:
        record = dict(zip(header, parts))
        amount = record.pop('amount', '0')
        result.append({
            'id': str(record.get('id', '')),
            'customer': record.get('customer', ''),
            'amount_cents': _parse_amount_cents(amount),
        })
    return result
