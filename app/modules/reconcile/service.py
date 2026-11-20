from decimal import Decimal
from .ledger import ledger


def compare(accepted, payload, excluded=()):
    """Compare the accepted business account with the independent ledger.

    ``excluded`` keys were quarantined for missing on-site evidence.  They are
    reported as ISOLATED and removed from both totals, so the independent
    difference and the deliverable are computed on one and the same basis and
    no default value leaks into the formal difference.
    """
    expected = ledger(payload)
    actual = {row['key']: (Decimal(row['amount']), row['line']) for row in accepted}
    excluded = {key for key in excluded if key not in actual}
    rows, matches, isolated = [], 0, 0
    for key in sorted(actual.keys() | expected.keys() | excluded):
        value, line = actual.get(key, (None, None))
        book, book_line = expected.get(key, (None, None))
        if key in excluded:
            isolated += 1
            rows.append({'key': key, 'amount': None,
                         'reference': str(book) if book is not None else None,
                         'delta': None, 'line': None, 'book_line': book_line, 'code': 'ISOLATED'})
            continue
        delta = (value or Decimal(0)) - (book or Decimal(0))
        reason = ('MISSING_BOOK' if book is None else 'MISSING_RESULT' if value is None else
                  'AMOUNT_DELTA' if delta else 'MATCH')
        matches += reason == 'MATCH'
        rows.append({'key': key, 'amount': str(value) if value is not None else None,
                     'reference': str(book) if book is not None else None, 'delta': str(delta),
                     'line': line, 'book_line': book_line, 'code': reason})
    actual_total = sum((pair[0] for pair in actual.values()), Decimal(0))
    book_total = sum((value for key, (value, _) in expected.items() if key not in excluded), Decimal(0))
    compared = len(actual.keys() | expected.keys() | excluded)
    return {'rows': rows, 'matched': matches, 'mismatched': compared - matches - isolated,
            'isolated': isolated, 'excluded': sorted(excluded),
            'actual': str(actual_total), 'expected': str(book_total), 'delta': str(actual_total - book_total)}
