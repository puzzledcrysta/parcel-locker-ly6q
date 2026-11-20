import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / 'sample_data'
DB = Path(os.getenv('WORKBENCH_DB', str(ROOT/'state/ledger.sqlite3')))
TITLE = '格口交接账'
SLUG = 'parcel-locker'
KEY = '保管单'
FIELDS = ('格口事件', '结算截止分钟')
# 门磁口径 2.0 强制要求的现场证据字段。
EVIDENCE_FIELDS = ('现场来源', '事件原因')
EVIDENCE_CODES = {'现场来源': 'SOURCE_MISSING', '事件原因': 'REASON_MISSING'}
ROLE = '驿站运营稽核员'
UNIT = '占用分钟'
SIGNATURE = '门磁门片'
RULE_VERSION = 'parcel-locker-1.0'
# 受支持的字段口径。1.0 兼容旧班次，2.0 要求现场来源与事件原因。
CALIBERS = {
    '1.0': {'label': '门磁口径 1.0（旧班次兼容）', 'fields': (), 'legacy': True},
    '2.0': {'label': '门磁口径 2.0', 'fields': EVIDENCE_FIELDS, 'legacy': False},
}
CURRENT_CALIBER = '2.0'
LEGACY_CALIBER = '1.0'
# 只因新口径现场证据缺失而隔离的原因码。
ISOLATION_CODES = ('SOURCE_MISSING', 'REASON_MISSING', 'EVIDENCE_MISSING')
TABS = {'intake': '来源采信', 'contract': '字段解释', 'quality': '隔离裁决', 'domain': '门磁回放', 'reconcile': '独立对账', 'runs': '批次复算', 'review': '交付复核'}
