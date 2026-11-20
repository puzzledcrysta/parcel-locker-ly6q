import json
from hashlib import sha256
from app.errors import DataError
from app.store import connection


def lookup(db, run_id):
    row = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
    if row is None:
        raise DataError('RUN_UNKNOWN', '没有此批次', 404)
    return row


def fetch(run_id):
    with connection() as db:
        return lookup(db, run_id)


def persist(run_id, source, book, result, created):
    with connection() as db:
        db.execute('INSERT OR IGNORE INTO runs VALUES (?,?,?,?,?)',
                   (run_id, source, book, json.dumps(result, ensure_ascii=False), created))
        return lookup(db, run_id)


def history():
    with connection() as db:
        return [dict(row) for row in db.execute(
            'SELECT id,created FROM runs ORDER BY created DESC,id DESC LIMIT 50')]


def prior(source, book):
    """Latest stored batch over the very same two inputs, whatever caliber."""
    source_hash, book_hash = sha256(source).hexdigest(), sha256(book).hexdigest()
    with connection() as db:
        for row in db.execute('SELECT * FROM runs ORDER BY created DESC,id DESC'):
            if sha256(row['source']).hexdigest() != source_hash:
                continue
            if sha256(row['book']).hexdigest() != book_hash:
                continue
            return row
    return None
