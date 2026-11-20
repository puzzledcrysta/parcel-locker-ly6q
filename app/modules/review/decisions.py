import json
from datetime import datetime, timezone
from app.errors import DataError
from app.store import connection
from app.modules.runs.repository import lookup


def timeline(run_id):
    with connection() as db:
        lookup(db, run_id)
        return list(map(dict, db.execute(
            'SELECT version,decision,note,changed FROM reviews WHERE run_id=? ORDER BY version DESC',
            (run_id,))))


def blockers(run):
    """Reasons this batch may not be accepted without a review note."""
    reasons = []
    if run['book']['mismatched']:
        reasons.append('独立账仍有差异')
    if run['quarantine']:
        reasons.append('存在隔离记录')
    return reasons


def decide(run_id, version, decision, note):
    note = note.strip()
    if decision not in {'确认', '退回'}:
        raise DataError('REVIEW_DECISION', '复核结论无效')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        run = json.loads(lookup(db, run_id)['result'])
        current = db.execute('SELECT COALESCE(MAX(version),0) FROM reviews WHERE run_id=?', (run_id,)).fetchone()[0]
        if current != version:
            raise DataError('STALE', '复核版本已过期，请刷新', 409)
        if (blockers(run) or decision == '退回') and not note:
            raise DataError('REVIEW_NOTE', '有差异时须填写复核意见')
        record = {'version': current + 1, 'decision': decision, 'note': note,
                  'changed': datetime.now(timezone.utc).isoformat()}
        db.execute('INSERT INTO reviews VALUES (?,?,?,?,?)', (run_id, *record.values()))
        return record
