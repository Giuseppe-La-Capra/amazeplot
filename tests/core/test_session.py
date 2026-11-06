import pytest

from amazeplot.core.action import Action
from amazeplot.core.errors import ParameterError, PlotError, SessionError
from amazeplot.core.session import DataSession
from amazeplot.operations.clean import DROPNA, FILLNA
from amazeplot.operations.decorate import TITLE
from amazeplot.operations.plot import LINE, SCATTER
from amazeplot.operations.select import HEAD, SELECT_COLUMNS


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
    with pytest.raises(ParameterError):
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


# -- Plot layers ---------------------------------------------------------


def test_add_layer(session):
    layer = session.add_layer(SCATTER, {"x": "age", "y": "score"})
    assert session.layers == (layer,)
    assert layer.params["x"] == "age"


def test_add_layer_requires_data():
    with pytest.raises(SessionError):
        DataSession().add_layer(TITLE, {"label": "t"})


def test_invalid_layer_is_not_added(session):
    with pytest.raises(ParameterError):
        session.add_layer(SCATTER, {"x": "nope", "y": "score"})
    with pytest.raises(PlotError):
        session.add_layer(
            SCATTER, {"x": "age", "y": "score", "color": "not-a-colour"}
        )
    assert session.layers == ()
    assert not session.can_undo


def test_undo_covers_steps_and_layers(session):
    session.apply(DROPNA, {})
    session.add_layer(LINE, {"y": "score"})
    session.undo()
    assert session.layers == ()
    assert len(session.steps) == 1
    session.undo()
    assert session.steps == ()
    session.redo()
    session.redo()
    assert len(session.layers) == 1


def test_layers_survive_data_steps(session):
    session.add_layer(LINE, {"y": "score"})
    session.apply(SELECT_COLUMNS, {"items": ["name"]})
    assert len(session.layers) == 1


def test_remove_and_clear_layers(session):
    session.add_layer(TITLE, {"label": "first"})
    session.add_layer(TITLE, {"label": "second"})
    session.remove_layer(0)
    assert [layer.params["label"] for layer in session.layers] == ["second"]
    session.clear_layers()
    assert session.layers == ()
    with pytest.raises(SessionError):
        session.clear_layers()
    with pytest.raises(SessionError):
        session.remove_layer(0)


def test_load_resets_layers(session, people):
    session.add_layer(TITLE, {"label": "t"})
    session.load(people)
    assert session.layers == ()


def test_perform_dispatches_by_action_type(session):
    session.perform(DROPNA, {})
    session.perform(TITLE, {"label": "t"})
    assert len(session.steps) == 1
    assert len(session.layers) == 1


def test_perform_rejects_other_actions(session):
    class Other(Action):
        def to_code(self, params, variable="df"):
            return ""

    with pytest.raises(TypeError):
        session.perform(Other("k", "K", "C", ""), {})
