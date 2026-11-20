from base64 import b64encode
from fastapi import APIRouter
from app.inputs import Paired, Replay
from .repository import fetch, history
from .service import run, replay, get

router = APIRouter()


@router.post('/api/runs')
def create(source: Paired):
    return run(source.raw(), source.ledger(), source.caliber)


@router.get('/api/runs')
def list_runs():
    return history()


@router.get('/api/runs/{run_id}')
def detail(run_id: str):
    return get(run_id)


@router.post('/api/runs/{run_id}/replay')
def again(run_id: str, request: Replay | None = None):
    return replay(run_id, request.caliber if request else None)


@router.get('/api/runs/{run_id}/source')
def source_inputs(run_id: str):
    record = fetch(run_id)
    return {'data_base64': b64encode(record['source']).decode(),
            'book_base64': b64encode(record['book']).decode()}
