from amazeplot.core.errors import OperationError
from amazeplot.gui.operation_dialog import OperationDialog
from amazeplot.operations.select import QUERY
from amazeplot.operations.transform import SORT_VALUES

COLUMNS = ["name", "age"]


def _dialog(qtbot, operation, callback=lambda params: None):
    dialog = OperationDialog(operation, COLUMNS, callback)
    qtbot.addWidget(dialog)
    return dialog


def test_preview_shows_validation_message(qtbot):
    dialog = _dialog(qtbot, SORT_VALUES)
    assert "required" in dialog.preview_text()


def test_preview_updates_with_input(qtbot):
    dialog = _dialog(qtbot, SORT_VALUES)
    dialog.editor("by").set_checked(["age"])
    assert dialog.preview_text() == "df = df.sort_values(by=['age'])"


def test_accept_calls_callback(qtbot):
    received = []
    dialog = _dialog(qtbot, QUERY, received.append)
    dialog.editor("expr").set_text("age > 3")
    dialog._on_accepted()
    assert received == [{"expr": "age > 3"}]
    assert dialog.result() == OperationDialog.DialogCode.Accepted


def test_error_keeps_dialog_open(qtbot):
    def fail(params):
        raise OperationError("boom")

    dialog = _dialog(qtbot, QUERY, fail)
    dialog._on_accepted()
    assert dialog.error_text() == "boom"
    assert dialog.result() != OperationDialog.DialogCode.Accepted
