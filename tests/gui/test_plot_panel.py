import pytest

from amazeplot.core.plotting import Layer
from amazeplot.gui.plot_panel import PlotPanel
from amazeplot.operations.decorate import TITLE
from amazeplot.operations.plot import LINE


@pytest.fixture
def panel(qtbot):
    panel = PlotPanel()
    qtbot.addWidget(panel)
    return panel


def _line(column):
    return Layer(LINE, {"x": None, "y": column})


def test_empty_panel_shows_hint(panel):
    panel.show_plot(None, ())
    assert panel.axes() is None
    assert "Plot category" in panel.message_text()


def test_layers_are_drawn_and_listed(panel, people):
    layers = (_line("score"), Layer(TITLE, {"label": "People"}))
    panel.show_plot(people, layers)
    assert len(panel.axes().get_lines()) == 1
    assert panel.axes().get_title() == "People"
    assert panel.layer_labels() == ["1. Line", "2. Title"]
    assert panel.message_text() == ""


def test_failing_layer_is_reported(panel, people):
    panel.show_plot(people, (_line("score"), _line("gone")))
    assert "Line failed" in panel.message_text()
    assert len(panel.axes().get_lines()) == 1


def test_remove_signal_carries_selected_row(panel, people, qtbot):
    panel.show_plot(people, (_line("score"), _line("age")))
    panel.select_layer(1)
    with qtbot.waitSignal(panel.remove_layer_requested) as blocker:
        panel.remove_selected_layer()
    assert blocker.args == [1]
