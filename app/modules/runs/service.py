import json
from datetime import datetime, timezone
from time import perf_counter
from app.errors import CaliberError, DataError
from app.caliber import stored as caliber_view
from app.manifest import manifest
from app.pipeline import execute
from .repository import fetch, persist, prior


def view(result):
    """Normalise a stored result for reading, marking pre-change batches legacy."""
    if result.get('caliber') is None:
        result = dict(result)
        result['caliber'] = caliber_view(result)
    return result


def run(source, book, version=None):
    started = perf_counter()
    try:
        result = execute(source, book, version)
    except DataError as error:
        # A failed caliber switch keeps the previous formal conclusion open
        # instead of replacing it with a partial or defaulted reading.
        if error.code != 'CALIBER':
            raise
        previous = prior(source, book)
        if previous is None:
            raise
        kept = json.loads(previous['result'])
        raise CaliberError(error.code, str(error), error.status,
                           preserved=preserved_view(kept)) from error
    created = datetime.now(timezone.utc).isoformat()
    proof = manifest(source, book, result['caliber']['version'])
    proof.update(elapsed_ms=round((perf_counter() - started) * 1000, 2), created=created)
    result['manifest'] = proof
    record = persist(proof['run_id'], source, book, result, created)
    return view(json.loads(record['result']))


def preserved_view(result):
    """The older formal conclusion, reopened unchanged for the reviewer."""
    kept = view(result)
    kept['preserved'] = True
    return kept


def replay(run_id, version=None):
    old = fetch(run_id)
    # Default replay keeps the caliber the batch was originally read under;
    # a batch stored before versioning carries no block and is re-detected.
    if version is None:
        version = json.loads(old['result']).get('caliber', {}).get('version')
    return run(old['source'], old['book'], version)


def get(run_id):
    return view(json.loads(fetch(run_id)['result']))
