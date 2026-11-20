from fastapi import APIRouter
from app.caliber import resolve, supported
from app.inputs import Source
from app.modules.intake.service import intake
from app.modules.contract.service import normalize
from .schema import ALIASES, REQUIRED, V2_REQUIRED

router = APIRouter()


@router.get('/api/calibers')
def calibers():
    return supported()


@router.get('/api/contract')
def fields():
    return {'required': REQUIRED, 'required_v2': V2_REQUIRED, 'aliases': ALIASES}


@router.post('/api/contract')
def apply(source: Source):
    raw = intake(source.raw())
    version = resolve(raw['header'], source.caliber)
    accepted, rejected = normalize(raw, version)
    return {'accepted': accepted, 'rejected': rejected, 'caliber': version}
