from app.errors import DataError
from app.evidence import distribution
from app.settings import CALIBERS, CURRENT_CALIBER, EVIDENCE_FIELDS, ISOLATION_CODES, LEGACY_CALIBER


def describe(version):
    spec = CALIBERS[version]
    return {'version': version, 'label': spec['label'],
            'fields': list(spec['fields']), 'legacy': spec['legacy']}


def supported():
    return {'current': CURRENT_CALIBER,
            'versions': [describe(version) for version in CALIBERS]}


def resolve(header, requested=None):
    """Decide which caliber a batch is read under.

    Detection is driven by the evidence columns, never by filling values:
    a source carrying either new column must carry both.  An explicit
    request that cannot be honoured is a failed caliber switch rather
    than a silent fallback to the other version.
    """
    present = [field for field in EVIDENCE_FIELDS if field in header]
    partial = bool(present) and len(present) != len(EVIDENCE_FIELDS)
    detected = CURRENT_CALIBER if len(present) == len(EVIDENCE_FIELDS) else LEGACY_CALIBER
    if requested is None:
        if partial:
            raise DataError('CALIBER', '现场来源与事件原因须同时提供，不能只补其中一列')
        return detected
    if requested not in CALIBERS:
        raise DataError('CALIBER', f'没有此口径 {requested}')
    if requested == CURRENT_CALIBER:
        if partial:
            raise DataError('CALIBER', '现场来源与事件原因须同时提供，不能只补其中一列')
        if not present:
            raise DataError('CALIBER', '来源缺少现场来源与事件原因，不能切换到新口径', 409)
        return CURRENT_CALIBER
    if present:
        raise DataError('CALIBER', '来源已含新口径证据字段，不能降级按旧口径复算', 409)
    return LEGACY_CALIBER


def block(version, requested=None, findings=()):
    """Reviewer-facing statement of what this batch was read under."""
    isolated = [row for row in findings if row.get('code') in ISOLATION_CODES]
    return {**describe(version),
            'requested': requested,
            'source': 'requested' if requested else 'detected',
            'isolated': isolated,
            'isolated_count': len(isolated),
            'reasons': distribution(isolated),
            'assumed': False}


def stored(result):
    """Caliber of a persisted batch, including runs written before the change."""
    found = result.get('caliber')
    if found:
        return found
    return {**describe(LEGACY_CALIBER), 'requested': None, 'source': 'stored',
            'isolated': [], 'isolated_count': 0, 'reasons': {}, 'assumed': True}
