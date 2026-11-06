import pandas as pd
import pytest
from PySide6.QtCore import Qt

from amazeplot.gui.data_view import DataView

TOTAL = 2_500


@pytest.fixture
def view(qtbot):
    view = DataView()
    qtbot.addWidget(view)
    view.set_frame(pd.DataFrame({"n": range(TOTAL)}))
    return view


def _shown(view):
    """Return the first and last value shown in the table."""
    model = view.model
    return model.frame["n"].iloc[0], model.frame["n"].iloc[-1]


def test_only_one_page_reaches_the_model(view):
    assert view.model.rowCount() == 1_000
    assert _shown(view) == (0, 999)
    assert view.range_text() == "Showing rows 1\N{EN DASH}1,000 of 2,500"


def test_next_and_previous(view):
    view.next_page()
    assert _shown(view) == (1_000, 1_999)
    view.next_page()
    assert _shown(view) == (2_000, 2_499)
    view.next_page()  # Already on the last page: nothing changes.
    assert _shown(view) == (2_000, 2_499)
    view.previous_page()
    assert _shown(view) == (1_000, 1_999)


def test_go_to_row_counts_from_one(view):
    view.go_to_row(42)
    assert _shown(view) == (41, 1_040)
    view.go_to_row(10_000)  # Past the end: show from the last row.
    assert _shown(view) == (2_499, 2_499)


def test_page_size(view):
    view.set_page_size(100)
    assert view.model.rowCount() == 100
    with pytest.raises(ValueError):
        view.set_page_size(7)


def test_row_labels_are_the_dataframe_index(view):
    view.set_frame(pd.DataFrame({"n": [1, 2]}, index=["x", "y"]))
    assert view.model.headerData(1, Qt.Orientation.Vertical) == "y"


def test_position_survives_data_steps(view):
    view.go_to_row(1_501)
    view.set_frame(pd.DataFrame({"n": range(TOTAL)}))
    assert view.window.start == 1_500
    view.set_frame(pd.DataFrame({"n": range(10)}))  # Shorter table.
    assert view.window.start == 9


def test_no_data(view):
    view.set_frame(None)
    assert view.model.rowCount() == 0
    assert view.range_text() == ""
