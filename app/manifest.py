from hashlib import sha256
from app.settings import RULE_VERSION


def manifest(raw, book, version=None):
    source_hash, book_hash = sha256(raw).hexdigest(), sha256(book).hexdigest()
    # The run identity covers the caliber so a re-read under another field
    # definition can never be mistaken for the same batch.
    identity = f'{RULE_VERSION}:{version or "auto"}:{source_hash}:{book_hash}'
    run_id = sha256(identity.encode()).hexdigest()
    return {'run_id': run_id, 'source_sha256': source_hash, 'book_sha256': book_hash,
            'version': RULE_VERSION, 'parameters': {'mode': '独立复算', 'caliber': version or 'auto'}}
