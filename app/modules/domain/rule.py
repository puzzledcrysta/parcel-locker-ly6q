from decimal import Decimal
from app.errors import DataError
from .values import whole, parts


TRANSITIONS = {('空','IN'): '存件', ('存件','OPEN'): '门开', ('门开','CLOSE'): '门闭',
               ('门闭','OPEN'): '门开', ('门闭','PICK'): '空'}


def evaluate(row):
    cutoff = whole(row['结算截止分钟'],0,10080)
    seen, entries, entries_at = {}, [], set()
    for item in parts(row['格口事件']):
        fields = item.split(':')
        if len(fields) != 3 or not fields[2]:
            raise DataError('BUSINESS', f'门磁事件缺列 {item}')
        stamp, action, key = fields
        minute = whole(stamp,0,10080)
        if key in seen:
            if seen[key] != (minute,action):
                raise DataError('BUSINESS', f'同事件号内容冲突 {key}')
            continue
        seen[key] = (minute,action)
        if minute < cutoff:
            if minute in entries_at:
                raise DataError('BUSINESS', f'同一时刻多个门磁事件 {minute}')
            entries_at.add(minute)
            entries.append((minute,action,key))
    state, start, balance, proof = '空', None, 0, []
    for minute,action,key in sorted(entries):
        next_state = TRANSITIONS.get((state,action))
        if next_state is None:
            raise DataError('BUSINESS', f'状态跳转非法 {key} {state}→{action}')
        state = next_state
        if action == 'IN':
            start = minute
        elif action == 'PICK':
            balance += minute-start
            proof.append((key,minute-start,'分钟'))
            start = None
    if start is not None:
        balance += cutoff-start
        proof.append(('截止未取',cutoff-start,'分钟'))
    return Decimal(balance), proof
