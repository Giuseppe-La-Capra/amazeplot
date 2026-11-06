from amazeplot.core.errors import OperationError
from amazeplot.gui.action_dialog import ActionDialog
from amazeplot.operations.select import QUERY
from amazeplot.operations.transform import SORT_VALUES

COLUMNS = ["name", "age"]


def _dialog(qtbot, action, callback=lambda params: None):
    dialog = ActionDialog(action, COLUMNS, callback)
    qtbot.addWidget(dialog)
    return dialog


def test_preview_shows_validation_message(qtbot):
    dialog = _dialog(qtbot, SORT_VALUES)
    assert "required" in dialog.preview_text()


def test_preview_updates_with_input(qtbot):
    dialog = _dialog(qtbot, SORT_VALUES)
    dialog.set_values({"by": ["age"]})
    assert dialog.preview_text() == "df = df.sort_values(by=['age'])"


def test_accept_calls_callback(qtbot):
    received = []
    dialog = _dialog(qtbot, QUERY, received.append)
    dialog.set_values({"expr": "age > 3"})
    dialog.confirm()
    assert received == [{"expr": "age > 3"}]
    assert dialog.result() == ActionDialog.DialogCode.Accepted


def test_error_keeps_dialog_open(qtbot):
    def fail(params):
        raise OperationError("boom")

    dialog = _dialog(qtbot, QUERY, fail)
    dialog.confirm()
    assert dialog.error_text() == "boom"
    assert dialog.result() != ActionDialog.DialogCode.Accepted


def test_help_button_only_with_callback(qtbot):
    assert not _dialog(qtbot, QUERY).has_help()
    calls = []
    dialog = ActionDialog(
        QUERY,
        COLUMNS,
        lambda params: None,
        help_callback=lambda: calls.append(1),
    )
    qtbot.addWidget(dialog)
    assert dialog.has_help()
    dialog.request_help()
    assert calls == [1]
