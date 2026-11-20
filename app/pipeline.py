from app.caliber import block, resolve
from app.evidence import distribution
from app.modules.intake.service import intake
from app.modules.contract.service import normalize
from app.modules.quality.service import inspect
from app.modules.domain.service import calculate
from app.modules.reconcile.service import compare


def stages(source, version=None):
    raw = intake(source)
    caliber = resolve(raw['header'], version)
    contract, rejected = normalize(raw, caliber)
    quality = inspect(contract, rejected)
    accepted, domain_bad = calculate(quality['ready'])
    bad = sorted([*quality['rejected'], *domain_bad], key=lambda row: row['line'])
    return {'intake': raw, 'contract': contract, 'quality': quality, 'accepted': accepted,
            'domain_bad': domain_bad, 'rejected': bad, 'caliber': caliber, 'requested': version}


def execute(source, book, version=None):
    result = stages(source, version)
    raw, accepted, bad = (result[key] for key in ('intake', 'accepted', 'rejected'))
    suppressed = result['quality']['suppressed']
    counts = {'input': raw['input_count'], 'accepted': len(accepted), 'rejected': len(bad),
              'suppressed': len(suppressed), 'blank': len(raw['blank_lines']),
              'repeated_header': len(raw['header_lines'])}
    balanced = counts['input'] == sum(value for key, value in counts.items() if key != 'input')
    if not balanced:
        raise RuntimeError('来源记录数量无法闭合')
    excluded = sorted({row['key'] for row in result['quality']['evidence_missing']})
    return {'counts': counts, 'balanced': balanced, 'accepted': accepted, 'quarantine': bad,
            'suppressed': suppressed, 'reasons': distribution(bad),
            'book': compare(accepted, book, excluded), 'encoding': raw['encoding'],
            'caliber': block(result['caliber'], result.get('requested'), bad)}
