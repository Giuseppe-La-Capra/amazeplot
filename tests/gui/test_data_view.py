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


def test_info_panel_describes_selected_cell(view):
    assert view.info_panel.column_fields() == {}  # Only the hint so far.
    view.next_page()
    view.select_cell(5, 0)
    column = view.info_panel.column_fields()
    assert column["Name"] == "n"
    assert column["Type (dtype)"] == "int64"
    assert column["Maximum"] == "2499"  # Whole table, not just the page.
    row = view.info_panel.row_fields()
    assert row["Position"] == "1,006 of 2,500"
    assert row["n"] == "1005"


def test_info_panel_clears_when_the_page_changes(view):
    view.select_cell(0, 0)
    assert view.info_panel.row_fields()
    view.next_page()
    assert view.info_panel.row_fields() == {}


def test_columns_fit_their_contents_once(qtbot):
    view = DataView()
    qtbot.addWidget(view)
    view.set_frame(pd.DataFrame({"short": [1], "long": ["x" * 30]}))
    assert view.column_width(1) > view.column_width(0)

    view.set_column_width(1, 40)
    view.set_frame(pd.DataFrame({"short": [2], "long": ["y" * 30]}))
    assert view.column_width(1) == 40  # Same columns: manual width kept.


def test_very_long_values_are_capped(qtbot):
    view = DataView()
    qtbot.addWidget(view)
    view.set_frame(pd.DataFrame({"long": ["x" * 500]}))
    assert view.column_width(0) <= 320
