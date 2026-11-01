"""AcmeCSV invoice parser."""

import re


def _parse_csv_line(line):
    """Parse a single CSV line with double-quote field quoting."""
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
                        i += 1
                        break
                else:
                    buf.append(line[i])
                    i += 1
            fields.append(''.join(buf))
            if i < n and line[i] == ',':
                i += 1
        else:
            # Unquoted field
            j = i
            while j < n and line[j] != ',':
                j += 1
            fields.append(line[i:j])
            i = j + 1 if j < n else j
    # Trailing comma produces empty field
    if n > 0 and line[-1] == ',':
        fields.append('')
    return fields


def _parse_amount_cents(amount):
    """Convert currency string to integer cents."""
    s = amount.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1]
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '').strip()
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
    if not text or not text.strip():
        return []

    # Split into records respecting quoted newlines
    records = []
    field = []
    row_fields = []
    i = 0
    n = len(text)
    in_quotes = False
    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')
                    i += 2
                    continue
                else:
                    in_quotes = False
                    i += 1
                    continue
            else:
                field.append(ch)
                i += 1
                continue
        else:
            if ch == '"':
                in_quotes = True
                i += 1
                continue
            if ch == ',':
                row_fields.append(''.join(field))
                field = []
                i += 1
                continue
            if ch == '\n' or (ch == '\r' and (i + 1 >= n or text[i + 1] != '\n')):
                row_fields.append(''.join(field))
                field = []
                if any(f.strip() for f in row_fields):
                    records.append(row_fields)
                row_fields = []
                i += 1
                continue
            if ch == '\r':
                i += 1
                continue
            field.append(ch)
            i += 1
    # last field/row
    if field or row_fields:
        row_fields.append(''.join(field))
        if any(f.strip() for f in row_fields):
            records.append(row_fields)

    if not records:
        return []

    header = [h.strip() for h in records[0]]
    rows = []
    for parts in records[1:]:
        # pad/truncate to header length
        while len(parts) < len(header):
            parts.append('')
        record = {header[j]: parts[j] for j in range(len(header))}
        amount = record.pop('amount', '0')
        rows.append({
            'id': str(record.get('id', '')),
            'customer': record.get('customer', ''),
            'amount_cents': _parse_amount_cents(amount),
        })
    return rows
