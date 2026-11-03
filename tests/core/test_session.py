import pytest

from amazeplot.core.errors import OperationError, SessionError
from amazeplot.core.session import DataSession
from amazeplot.operations.clean import DROPNA, FILLNA
from amazeplot.operations.select import HEAD


@pytest.fixture
def session(people):
    session = DataSession()
    session.load(people)
    return session


def test_new_session_is_empty():
    session = DataSession()
    assert not session.has_data
    assert session.frame is None
    with pytest.raises(SessionError):
        session.apply(HEAD, {})


def test_apply_records_step(session):
    result = session.apply(HEAD, {"n": 2})
    assert len(result) == 2
    assert session.frame is result
    assert [step.operation for step in session.steps] == [HEAD]
    assert session.steps[0].params == {"n": 2}


def test_failed_apply_leaves_session_unchanged(session):
    frame = session.frame
    with pytest.raises(OperationError):
        session.apply(HEAD, {"n": -5})
    assert session.frame is frame
    assert session.steps == ()


def test_undo_and_redo(session):
    original = session.frame
    after = session.apply(DROPNA, {})
    session.undo()
    assert session.frame is original
    assert session.can_redo
    session.redo()
    assert session.frame is after
    assert not session.can_redo


def test_apply_clears_redo_stack(session):
    session.apply(DROPNA, {})
    session.undo()
    session.apply(HEAD, {})
    assert not session.can_redo


def test_undo_redo_on_empty_history(session):
    with pytest.raises(SessionError):
        session.undo()
    with pytest.raises(SessionError):
        session.redo()


def test_value_parameters_are_coerced_once(session):
    # A quoted number must stay a string: coercing twice would turn
    # "'0'" into "0" and then into the integer 0.
    session.apply(FILLNA, {"value": "'0'", "column": "city"})
    assert session.steps[0].params["value"] == "0"


def test_listeners_are_notified(session):
    calls = []
    unsubscribe = session.subscribe(lambda: calls.append(1))
    session.apply(HEAD, {})
    session.undo()
    unsubscribe()
    session.redo()
    assert len(calls) == 2
