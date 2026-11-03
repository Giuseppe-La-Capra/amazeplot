import pytest

from amazeplot.core.io import save_dataframe
from amazeplot.core.session import DataSession
from amazeplot.gui.main_window import MainWindow
from amazeplot.operations import build_default_registry
from amazeplot.operations.clean import DROPNA


@pytest.fixture
def window(qtbot):
    window = MainWindow(DataSession(), build_default_registry())
    qtbot.addWidget(window)
    return window


@pytest.fixture
def csv_path(people, tmp_path):
    path = tmp_path / "people.csv"
    save_dataframe(people, path)
    return path


def test_starts_empty(window):
    assert window.model.rowCount() == 0
    assert window.windowTitle() == "amazeplot"


def test_open_file_shows_data(window, csv_path, people):
    assert window.open_file(csv_path)
    assert window.model.rowCount() == len(people)
    assert "people.csv" in window.windowTitle()
    assert "read_csv" in window.history_panel.script()
    assert window.status_text() == "5 rows x 4 columns"


def test_dialog_applies_operation(window, csv_path):
    window.open_file(csv_path)
    dialog = window.create_operation_dialog(DROPNA)
    dialog._on_accepted()
    assert window.model.rowCount() == 3
    assert window.history_panel.step_labels() == ["1. Drop missing values"]
    assert "df = df.dropna()" in window.history_panel.script()


def test_operations_panel_filter(window):
    panel = window.operations_panel
    panel.set_filter("duplicat")
    assert panel.visible_operation_keys() == ["drop_duplicates"]
    panel.set_filter("")
    assert len(panel.visible_operation_keys()) > 1


def test_undo_redo_actions(window, csv_path):
    window.open_file(csv_path)
    window.create_operation_dialog(DROPNA)._on_accepted()
    window._undo_action.trigger()
    assert window.model.rowCount() == 5
    assert not window._undo_action.isEnabled()
    window._redo_action.trigger()
    assert window.model.rowCount() == 3
