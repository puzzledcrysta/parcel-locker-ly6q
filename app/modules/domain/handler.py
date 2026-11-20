from fastapi import APIRouter
from app.inputs import Source
from app.pipeline import stages

router = APIRouter()


@router.post('/api/domain')
def recalculate(source: Source):
    result = stages(source.raw(), source.caliber)
    return {key: result[key] for key in ('accepted', 'rejected', 'domain_bad', 'caliber')}
