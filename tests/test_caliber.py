import json
from base64 import b64encode
from pathlib import Path

import pytest

from app import settings
from app.caliber import resolve
from app.errors import DataError
from app.pipeline import execute
from app.settings import EVIDENCE_FIELDS

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def v2_source():
    return (ROOT / 'sample_data/shift_v2.csv').read_bytes()


@pytest.fixture
def v2_book():
    return (ROOT / 'sample_data/external_v2.csv').read_bytes()


def test_legacy_shift_still_recomputes_and_reconciles(source, book):
    result = execute(source, book)
    assert result['caliber']['version'] == '1.0'
    assert result['caliber']['legacy'] is True
    assert result['caliber']['isolated_count'] == 0
    # A legacy batch keeps a complete, reconcilable account.
    assert result['counts']['accepted'] == 26
    assert result['book']['mismatched'] == 3


def test_new_shift_is_detected_and_isolates_missing_evidence(v2_source, v2_book):
    result = execute(v2_source, v2_book)
    assert result['caliber']['version'] == '2.0'
    gaps = {(row['key'], row['code']) for row in result['caliber']['isolated']}
    assert gaps == {('00202', 'SOURCE_MISSING'), ('00203', 'REASON_MISSING'),
                    ('00204', 'SOURCE_MISSING')}
    assert result['caliber']['isolated_count'] == 3
    assert result['caliber']['reasons'] == {'REASON_MISSING': 1, 'SOURCE_MISSING': 2}


def test_missing_evidence_never_defaults_into_the_difference(v2_source, v2_book):
    result = execute(v2_source, v2_book)
    accepted = {row['key'] for row in result['accepted']}
    # Isolated keys are absent from the accepted account ...
    assert accepted == {'00201', '00205', '00206'}
    # ... and marked ISOLATED rather than turned into a numeric delta.
    by_key = {row['key']: row for row in result['book']['rows']}
    for key in ('00202', '00203', '00204'):
        assert by_key[key]['code'] == 'ISOLATED' and by_key[key]['delta'] is None
    assert result['book']['isolated'] == 3
    assert result['book']['excluded'] == ['00202', '00203', '00204']


def test_book_totals_and_deltas_share_the_delivered_basis(v2_source, v2_book):
    result = execute(v2_source, v2_book)
    book = result['book']
    # The external total excludes isolated keys, so it matches the sum of the
    # numeric row deltas on the very same accepted basis.
    numeric = sum(int(row['delta']) for row in book['rows'] if row['delta'] is not None)
    assert int(book['delta']) == numeric
    assert book['expected'] == '11' and book['actual'] == '9'


def test_higher_revision_without_evidence_does_not_promote_older_one(v2_source, v2_book):
    result = execute(v2_source, v2_book)
    assert '00204' not in {row['key'] for row in result['accepted']}
    codes = [(row['key'], row['code']) for row in result['quarantine']]
    assert ('00204', 'SOURCE_MISSING') in codes


def test_explicit_switch_to_new_caliber_is_refused_for_legacy(source, book):
    with pytest.raises(DataError) as error:
        execute(source, book, '2.0')
    assert error.value.code == 'CALIBER' and error.value.status == 409


def test_review_requires_note_when_records_isolated(client, v2_source, v2_book):
    run = client.post('/api/runs', json={'data_base64': b64encode(v2_source).decode(),
                                         'book_base64': b64encode(v2_book).decode()}).json()
    rid = run['manifest']['run_id']
    bare = client.post(f'/api/review/{rid}', json={'version': 0, 'decision': '确认', 'note': ''})
    assert (bare.status_code, bare.json()['code']) == (422, 'REVIEW_NOTE')
    noted = client.post(f'/api/review/{rid}',
                        json={'version': 0, 'decision': '确认', 'note': '00204 待补现场来源'})
    assert noted.status_code == 200


def test_same_revision_with_different_evidence_is_a_conflict(v2_source):
    from app.modules.contract.service import normalize
    from app.modules.intake.service import intake
    from app.modules.quality.service import inspect

    lines = v2_source.decode('utf-8-sig').rstrip('\r\n').split('\r\n')
    fields = lines[1].split(',')
    alt = ','.join([*fields[:-1], '另一现场原因'])
    source = ('\r\n'.join([lines[0], lines[1], alt]) + '\r\n').encode('utf-8-sig')
    result = inspect(*normalize(intake(source), '2.0'))
    assert '00201' not in {row['key'] for row in result['ready']}
    assert [row['code'] for row in result['rejected']] == ['REV_CONFLICT', 'REV_CONFLICT']


def test_legacy_batch_without_stored_caliber_reads_as_legacy(client, source, book):
    import json
    import sqlite3
    from app import settings

    run = client.post('/api/runs', json={}).json()
    rid = run['manifest']['run_id']
    with sqlite3.connect(settings.DB) as db:
        row = db.execute('SELECT result FROM runs WHERE id=?', (rid,)).fetchone()
        stored = json.loads(row[0])
        stored.pop('caliber', None)
        db.execute('UPDATE runs SET result=? WHERE id=?',
                   (json.dumps(stored, ensure_ascii=False), rid))
    detail = client.get(f'/api/runs/{rid}').json()
    assert detail['caliber']['version'] == '1.0' and detail['caliber']['assumed'] is True
    exported = client.get(f'/api/export/{rid}').json()
    assert exported['caliber']['version'] == '1.0' and exported['caliber']['assumed'] is True
    replay = client.post(f'/api/runs/{rid}/replay')
    assert replay.status_code == 200
    assert replay.json()['caliber']['version'] == '1.0'


def test_legacy_caliber_cannot_be_forced_over_new_columns(v2_source, v2_book):
    with pytest.raises(DataError) as error:
        execute(v2_source, v2_book, '1.0')
    assert error.value.code == 'CALIBER'


def test_partial_evidence_columns_are_refused():
    with pytest.raises(DataError) as error:
        resolve(['保管单', '现场来源'])
    assert error.value.code == 'CALIBER'


def test_caliber_block_states_what_was_used(v2_source, v2_book):
    report = execute(v2_source, v2_book, '2.0')['caliber']
    assert report['requested'] == '2.0' and report['source'] == 'requested'
    assert report['fields'] == list(EVIDENCE_FIELDS)


def test_reconcile_endpoint_reports_same_basis(client, v2_source, v2_book):
    report = client.post('/api/reconcile', json={'data_base64': b64encode(v2_source).decode(),
                                                 'book_base64': b64encode(v2_book).decode()}).json()
    assert report['caliber']['version'] == '2.0'
    assert report['book']['isolated'] == report['caliber']['isolated_count'] == 3
    assert report['book']['excluded'] == ['00202', '00203', '00204']


def test_export_names_caliber_and_isolated_records(client, v2_source, v2_book):
    run = client.post('/api/runs', json={'data_base64': b64encode(v2_source).decode(),
                                         'book_base64': b64encode(v2_book).decode()}).json()
    proof = client.get(f"/api/export/{run['manifest']['run_id']}").json()
    assert proof['caliber']['version'] == '2.0'
    assert proof['caliber']['isolated_count'] == 3
    assert {row['key'] for row in proof['caliber']['isolated']} == {'00202', '00203', '00204'}


def test_failed_switch_reopens_previous_conclusion(client, source, book):
    first = client.post('/api/runs', json={}).json()
    before = client.get('/api/runs').json()
    failed = client.post('/api/runs', json={'caliber': '2.0'})
    assert failed.status_code == 409 and failed.json()['code'] == 'CALIBER'
    preserved = failed.json()['preserved']
    # The old formal conclusion is returned unchanged and stays persisted.
    assert preserved['manifest']['run_id'] == first['manifest']['run_id']
    assert preserved['caliber']['version'] == '1.0' and preserved['preserved'] is True
    assert client.get('/api/runs').json() == before


def test_other_failures_do_not_claim_a_preserved_conclusion(client):
    # A malformed source has the same empty JSON inputs as {}, but no
    # caliber failure, so it must surface plainly without a preserved view.
    response = client.post('/api/runs', json={'data': 'bad\na'})
    assert response.status_code == 422 and 'preserved' not in response.json()


def test_explicit_v2_run_cannot_replace_a_legacy_batch_silently(client, source, book):
    client.post('/api/runs', json={}).json()
    # Same source bytes, now forced to the new caliber.
    response = client.post('/api/runs', json={'caliber': '2.0',
                                              'data_base64': b64encode(source).decode()})
    assert response.status_code == 409
    assert response.json()['preserved']['counts']['accepted'] == 26
    assert response.json()['preserved']['caliber']['version'] == '1.0'
