from app.settings import KEY, FIELDS, EVIDENCE_FIELDS
from app.errors import DataError

REQUIRED = (KEY, '修订号', '提交时间', *FIELDS)
V2_REQUIRED = (*REQUIRED, *EVIDENCE_FIELDS)
ALIASES = {'业务编号': KEY, '版本': '修订号', '更新时刻': '提交时间', '备注': '原始备注'}
MISSING = {'', '-', 'n/a', 'null', '未知'}
# 现场证据字段不接受「无」这类空集合写法，不能用它代替真实来源。
EVIDENCE_MISSING = MISSING | {'无'}


def mapping(header, version='1.0'):
    names = [ALIASES.get(name, name) for name in header]
    required = V2_REQUIRED if version == '2.0' else REQUIRED
    if len(set(names)) != len(names) or set(required) - set(names):
        raise DataError('CONTRACT', '必需字段缺失或新旧字段重复')
    return names
