import json
from app.caliber import stored
from app.modules.runs.service import get
from .decisions import blockers, timeline


def bundle(run_id):
    history = timeline(run_id)
    run = get(run_id)
    # The export carries the caliber the batch was read under, the records it
    # isolated, and the single reconciliation basis behind the decision.
    return json.dumps({'manifest': run['manifest'], 'caliber': stored(run),
                       'counts': run['counts'], 'results': run['accepted'],
                       'quarantine': run['quarantine'], 'suppressed': run['suppressed'],
                       'reconciliation': run['book'], 'review': history,
                       'blockers': blockers(run)},
                      ensure_ascii=False, indent=2)
