import pandas as pd
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


class _Confirm:
    """Stand-in for the yes/no message box that records each question."""

    def __init__(self, answer):
        self.answer = answer
        self.questions = []

    def __call__(self, title, message):
        self.questions.append((title, message))
        return self.answer


@pytest.fixture
def pickle_path(people, tmp_path):
    path = tmp_path / "people.pkl"
    people.to_pickle(path)
    return path


@pytest.mark.parametrize("answer", [True, False])
def test_pickle_opens_only_after_confirmation(
    qtbot, session, pickle_path, people, answer
):
    confirm = _Confirm(answer)
    window = MainWindow(session, build_default_registry(), confirm=confirm)
    qtbot.addWidget(window)

    assert window.open_file(pickle_path) is answer
    assert window.model.rowCount() == (len(people) if answer else 0)
    [(title, message)] = confirm.questions
    assert "pickle" in title.lower()
    assert "people.pkl" in message


def test_safe_formats_do_not_ask(qtbot, session, csv_path):
    confirm = _Confirm(False)
    window = MainWindow(session, build_default_registry(), confirm=confirm)
    qtbot.addWidget(window)
    assert window.open_file(csv_path)
    assert confirm.questions == []


def test_help_menu_is_last(window):
    assert window.menu_titles() == ["&File", "&Edit", "&Help"]


def test_show_help_opens_requested_page(window):
    assert window.help_window is None
    help_window = window.show_help("groupby")
    assert help_window.isVisible()
    assert help_window.current_key() == "groupby"
    assert window.show_help() is help_window


def test_action_dialog_help_button_opens_its_page(window, csv_path):
    window.open_file(csv_path)
    dialog = window.create_action_dialog(SCATTER)
    assert dialog.has_help()
    dialog.request_help()
    assert window.help_window.current_key() == SCATTER.key


def test_open_example_data(window, tmp_path):
    assert window.open_example_data(tmp_path)
    assert window.model.rowCount() == 12
    assert "amazeplot-example.csv" in window.history_panel.script()


def test_plot_is_drawn_only_when_visible(window, session, csv_path):
    window.open_file(csv_path)
    session.add_layer(SCATTER, {"x": "age", "y": "score"})
    assert window.current_tab() == DATA_TAB
    assert window.plot_is_stale()
    assert window.plot_panel.layer_labels() == ["1. Scatter"]
    assert window.plot_panel.axes() is None  # Not drawn while hidden.

    window.show_tab(PLOT_TAB)
    assert not window.plot_is_stale()
    assert len(window.plot_panel.axes().collections) == 1


def test_opening_a_file_starts_at_the_first_row(window, tmp_path):
    big = tmp_path / "big.csv"
    pd.DataFrame({"n": range(3_000)}).to_csv(big, index=False)
    window.open_file(big)
    window.data_view.next_page()
    window.open_file(big)
    assert window.data_view.window.start == 0
