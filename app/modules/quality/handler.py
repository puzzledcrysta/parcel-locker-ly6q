from fastapi import APIRouter
from app.caliber import resolve
from app.inputs import Source
from app.modules.intake.service import intake
from app.modules.contract.service import normalize
from .service import inspect

router = APIRouter()


@router.post('/api/quality')
def quality(source: Source):
    raw = intake(source.raw())
    return inspect(*normalize(raw, resolve(raw['header'], source.caliber)))
