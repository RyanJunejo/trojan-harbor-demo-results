'''AcmeCSV invoice parser.'''

import csv
import io


def _amount_to_cents(value):
    text = value.strip()
    negative = False
    if text.startswith('(') and text.endswith(')'):
        negative = True
        text = text[1:-1].strip()
    if text.startswith('$'):
        text = text[1:].strip()
    text = text.replace(',', '')
    if text.startswith('-'):
        negative = not negative
        text = text[1:].strip()
    if not text:
        raise ValueError('empty amount')
    if text.count('.') > 1:
        raise ValueError(f'invalid amount: {value!r}')
    if '.' in text:
        whole, fraction = text.split('.', 1)
    else:
        whole, fraction = text, ''
    if not whole:
        whole = '0'
    if not whole.isdigit() or (fraction and not fraction.isdigit()):
        raise ValueError(f'invalid amount: {value!r}')
    if len(fraction) > 2:
        raise ValueError(f'amount has more than two decimal places: {value!r}')
    cents = int(whole) * 100
    if fraction:
        cents += int(fraction.ljust(2, '0'))
    return -cents if negative else cents


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text))
    header = None
    for record in reader:
        if record:
            header = record
            break
    if header is None:
        return []
    rows = []
    for record in reader:
        if not record:
            continue
        if len(record) != len(header):
            raise ValueError(
                f'expected {len(header)} fields, got {len(record)}: {record!r}'
            )
        source = dict(zip(header, record))
        rows.append({
            'id': source['id'],
            'customer': source['customer'],
            'amount_cents': _amount_to_cents(source['amount']),
        })
    return rows
