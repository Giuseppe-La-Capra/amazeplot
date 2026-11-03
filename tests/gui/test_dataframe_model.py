import pandas as pd
from PySide6.QtCore import Qt

from amazeplot.gui.dataframe_model import MISSING_TEXT, DataFrameModel


def test_empty_model(qtbot):
    model = DataFrameModel()
    assert model.rowCount() == 0
    assert model.columnCount() == 0


def test_shape_and_values(qtbot, people):
    model = DataFrameModel()
    model.set_frame(people)
    assert model.rowCount() == len(people)
    assert model.columnCount() == len(people.columns)
    assert model.data(model.index(0, 0)) == "Ann"
    assert model.data(model.index(2, 2)) == MISSING_TEXT


def test_headers(qtbot, people):
    model = DataFrameModel()
    model.set_frame(people)
    horizontal = Qt.Orientation.Horizontal
    assert model.headerData(2, horizontal) == "age"
    assert "float64" in model.headerData(
        2, horizontal, Qt.ItemDataRole.ToolTipRole
    )
    assert model.headerData(1, Qt.Orientation.Vertical) == "1"


def test_numbers_are_right_aligned(qtbot, people):
    model = DataFrameModel()
    model.set_frame(people)
    role = Qt.ItemDataRole.TextAlignmentRole
    assert model.data(model.index(0, 3), role) & Qt.AlignmentFlag.AlignRight
    assert model.data(model.index(0, 0), role) & Qt.AlignmentFlag.AlignLeft


def test_set_frame_none_resets(qtbot):
    model = DataFrameModel()
    model.set_frame(pd.DataFrame({"a": [1]}))
    model.set_frame(None)
    assert model.rowCount() == 0
