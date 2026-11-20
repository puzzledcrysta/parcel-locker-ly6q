import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / 'sample_data'
DB = Path(os.getenv('WORKBENCH_DB', str(ROOT/'state/ledger.sqlite3')))
TITLE = '格口交接账'
SLUG = 'parcel-locker'
KEY = '保管单'
FIELDS = ('格口事件', '结算截止分钟')
ROLE = '驿站运营稽核员'
UNIT = '占用分钟'
SIGNATURE = '门磁门片'
RULE_VERSION = 'parcel-locker-1.0'
TABS = {'intake': '来源采信', 'contract': '字段解释', 'quality': '隔离裁决', 'domain': '门磁回放', 'reconcile': '独立对账', 'runs': '批次复算', 'review': '交付复核'}
