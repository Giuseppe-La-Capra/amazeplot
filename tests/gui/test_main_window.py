import pytest

from amazeplot.core.io import save_dataframe
from amazeplot.core.session import DataSession
from amazeplot.gui.main_window import DATA_TAB, PLOT_TAB, MainWindow
from amazeplot.operations import build_default_registry
from amazeplot.operations.clean import DROPNA
from amazeplot.operations.decorate import TITLE
from amazeplot.operations.plot import SCATTER


@pytest.fixture
def session():
    return DataSession()


@pytest.fixture
def window(qtbot, session):
    window = MainWindow(session, build_default_registry())
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
    dialog = window.create_action_dialog(DROPNA)
    dialog.confirm()
    assert window.model.rowCount() == 3
    assert window.history_panel.step_labels() == ["1. Drop missing values"]
    assert "df = df.dropna()" in window.history_panel.script()


def test_operations_panel_filter(window):
    panel = window.actions_panel
    panel.set_filter("duplicat")
    assert panel.visible_action_keys() == ["drop_duplicates"]
    panel.set_filter("")
    assert len(panel.visible_action_keys()) > 1


def test_undo_redo_actions(window, csv_path):
    window.open_file(csv_path)
    window.create_action_dialog(DROPNA).confirm()
    window._undo_action.trigger()
    assert window.model.rowCount() == 5
    assert not window._undo_action.isEnabled()
    window._redo_action.trigger()
    assert window.model.rowCount() == 3


def test_plot_call_adds_layer_and_shows_plot(window, csv_path):
    window.open_file(csv_path)
    dialog = window.create_action_dialog(SCATTER)
    dialog.set_values({"x": "age", "y": "score"})
    dialog.confirm()

    assert window.current_tab() == PLOT_TAB
    assert window.plot_panel.layer_labels() == ["1. Scatter"]
    assert "ax.scatter(df['age'], df['score'])" in (
        window.history_panel.script()
    )

    window.create_action_dialog(DROPNA).confirm()
    assert window.current_tab() == DATA_TAB


def test_clear_plot_and_undo(window, session, csv_path):
    window.open_file(csv_path)
    session.add_layer(TITLE, {"label": "t"})
    window.plot_panel.clear_requested.emit()
    assert window.plot_panel.layer_labels() == []
    window._undo_action.trigger()
    assert window.plot_panel.layer_labels() == ["1. Title"]
