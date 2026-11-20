from decimal import Decimal
import pytest
from app.errors import DataError
from app.modules.domain.rule import evaluate


def test_unordered(cases):
    # TRAP-13
    actual, evidence = evaluate(cases['unordered'])
    assert actual == Decimal('22')
    assert evidence and all(len(row)==3 for row in evidence)


def test_open(cases):
    actual, evidence = evaluate(cases['open'])
    assert actual == Decimal('25')


def test_two(cases):
    actual, evidence = evaluate(cases['two'])
    assert actual == Decimal('8')


def test_future(cases):
    actual, evidence = evaluate(cases['future'])
    assert actual == Decimal('0')


def test_jump(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['jump'])
    assert error.value.code in {'BUSINESS','NUMBER','RANGE','TIMESTAMP'}


def test_event_conflict(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['event_conflict'])
    assert error.value.code in {'BUSINESS','NUMBER','RANGE','TIMESTAMP'}


def test_same_minute(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['same_minute'])
    assert error.value.code in {'BUSINESS','NUMBER','RANGE','TIMESTAMP'}

