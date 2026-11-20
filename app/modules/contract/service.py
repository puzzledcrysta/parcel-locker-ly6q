from app.errors import DataError
from app.evidence import finding
from app.settings import KEY, FIELDS, EVIDENCE_FIELDS, EVIDENCE_CODES
from app.modules.domain.values import whole, instant
from .schema import mapping, REQUIRED, MISSING, EVIDENCE_MISSING


def evidence_gaps(values):
    """Fields whose on-site evidence is genuinely absent.

    Blank sentinels and the empty-set word 无 both count as absent; neither is
    replaced by a default because the gap changes the formal difference.
    """
    return [field for field in EVIDENCE_FIELDS
            if values[field].casefold() in EVIDENCE_MISSING]


def normalize(source, version='1.0'):
    names = mapping(source['header'], version)
    passed, rejected = [], list(source['rejected'])
    for record in source['rows']:
        values = dict(zip(names, record['values']))
        key = values[KEY]
        try:
            if any(values[k].casefold() in MISSING for k in REQUIRED):
                raise DataError('REQUIRED', '主键、修订号、时间和业务字段均须填写')
            rev = whole(values['修订号'], 1, 10**9)
            changed = instant(values['提交时间']).isoformat()
        except DataError as error:
            rejected.append(finding(dict(record, key=key), error.code, str(error)))
            continue
        row = {'key': key, 'revision': rev, 'time': changed, 'line': record['line'],
               'raw': record['raw'], 'fields': {field: values[field] for field in FIELDS},
               'note': values.get('原始备注', ''), 'caliber': version}
        if version == '2.0':
            row['evidence'] = {field: values[field] for field in EVIDENCE_FIELDS}
            # Kept, not dropped: version arbitration must see this revision
            # before the gap is judged, so a lower revision can never stand in.
            row['missing_evidence'] = evidence_gaps(values)
        passed.append(row)
    return passed, rejected


def gap_findings(record):
    return [finding(record, EVIDENCE_CODES[field], f'{field}为空，不按默认值计入正式差异')
            for field in record.get('missing_evidence', ())]
