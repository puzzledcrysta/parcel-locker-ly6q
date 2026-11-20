from app.evidence import distribution
from app.modules.contract.service import gap_findings
from .versions import split_versions


def inspect(records, rejected):
    ready, duplicate, conflicts = split_versions(records)
    # A winning revision without on-site evidence is quarantined rather
    # than defaulted; an older revision is never promoted to replace it.
    gaps, kept = [], []
    for record in ready:
        found = gap_findings(record)
        if found:
            gaps.extend(found)
        else:
            kept.append(record)
    quarantine = sorted([*rejected, *conflicts, *gaps], key=lambda row: row['line'])
    return {'ready': kept, 'suppressed': sorted(duplicate, key=lambda row: row['line']),
            'rejected': quarantine, 'reasons': distribution(quarantine),
            'evidence_missing': sorted(gaps, key=lambda row: row['line'])}
