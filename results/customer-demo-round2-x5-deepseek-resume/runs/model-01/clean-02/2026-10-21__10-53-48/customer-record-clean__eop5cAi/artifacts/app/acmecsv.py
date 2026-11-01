import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def parse(text):
    reader = csv.reader(io.StringIO(text))
    try:
        header = [name.strip() for name in next(reader)]
    except StopIteration:
        return []

    rows = []
    for values in reader:
        if not values or all(value == '' for value in values):
            continue

        record = dict(zip(header, values))
        amount_text = record['amount'].strip()
        negative = amount_text.startswith('(') and amount_text.endswith(')')
        if negative:
            amount_text = amount_text[1:-1].strip()

        amount_text = amount_text.replace('$', '').replace(',', '').strip()
        amount = Decimal(amount_text)
        if negative:
            amount = -amount

        cents = int((amount * 100).to_integral_value(rounding=ROUND_HALF_UP))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': cents,
        })

    return rows
