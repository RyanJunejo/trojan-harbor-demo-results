import csv
import io
from decimal import Decimal


def _amount_to_cents(amount):
    value = amount.strip()
    negative = value.startswith('(') and value.endswith(')')
    if negative:
        value = value[1:-1]
    value = value.replace('$', '').replace(',', '').strip()
    if not value:
        raise ValueError(f'Empty amount: {amount!r}')
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    records = list(csv.reader(io.StringIO(text, newline='')))
    if not records:
        return []

    header = [column.strip() for column in records[0]]
    columns = {name: header.index(name) for name in ('id', 'customer', 'amount')}

    rows = []
    for record in records[1:]:
        if not record or all(field == '' for field in record):
            continue

        rows.append({
            'id': record[columns['id']],
            'customer': record[columns['customer']],
            'amount_cents': _amount_to_cents(record[columns['amount']]),
        })

    return rows
