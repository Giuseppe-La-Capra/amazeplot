"""Qt table model that displays a pandas DataFrame read-only."""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandas.api import types as ptypes
from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
)
from PySide6.QtGui import QBrush, QColor

AnyIndex = QModelIndex | QPersistentModelIndex

MISSING_TEXT = "NaN"
"""Text displayed for missing values."""

_MISSING_COLOR = QColor(150, 150, 150)
_NUMBER_ALIGNMENT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_TEXT_ALIGNMENT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


def is_missing(value: Any) -> bool:
    """Return whether a cell value is a scalar missing value."""
    return ptypes.is_scalar(value) and bool(pd.isna(value))


def format_value(value: Any) -> str:
    """Return the text shown in a cell for ``value``."""
    if is_missing(value):
        return MISSING_TEXT
    return str(value)


class DataFrameModel(QAbstractTableModel):
    """Expose a DataFrame to a ``QTableView``.

    The model only reads cells that the view asks for, so large frames
    are cheap to display. It never modifies the DataFrame.
    """

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._frame = pd.DataFrame()
        self._numeric_columns: list[bool] = []

    @property
    def frame(self) -> pd.DataFrame:
        """Return the displayed DataFrame."""
        return self._frame

    def set_frame(self, frame: pd.DataFrame | None) -> None:
        """Display ``frame``, or an empty table when it is ``None``."""
        self.beginResetModel()
        self._frame = frame if frame is not None else pd.DataFrame()
        self._numeric_columns = [
            ptypes.is_numeric_dtype(dtype) and not ptypes.is_bool_dtype(dtype)
            for dtype in self._frame.dtypes
        ]
        self.endResetModel()

    # -- QAbstractTableModel interface -----------------------------------

    def rowCount(self, parent: AnyIndex | None = None) -> int:
        """Return the number of rows (zero for child indexes)."""
        if parent is not None and parent.isValid():
            return 0
        return len(self._frame.index)

    def columnCount(self, parent: AnyIndex | None = None) -> int:
        """Return the number of columns (zero for child indexes)."""
        if parent is not None and parent.isValid():
            return 0
        return len(self._frame.columns)

    def data(
        self, index: AnyIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """Return the cell text, colour or alignment for ``role``."""
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return format_value(self._cell(index))
        if role == Qt.ItemDataRole.ForegroundRole:
            if is_missing(self._cell(index)):
                return QBrush(_MISSING_COLOR)
            return None
        if role == Qt.ItemDataRole.TextAlignmentRole:
            numeric = self._numeric_columns[index.column()]
            return _NUMBER_ALIGNMENT if numeric else _TEXT_ALIGNMENT
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return column labels (with dtype tooltips) or row labels."""
        horizontal = orientation == Qt.Orientation.Horizontal
        if role == Qt.ItemDataRole.DisplayRole:
            labels = self._frame.columns if horizontal else self._frame.index
            return str(labels[section])
        if role == Qt.ItemDataRole.ToolTipRole and horizontal:
            return f"dtype: {self._frame.dtypes.iloc[section]}"
        return None

    def _cell(self, index: AnyIndex) -> Any:
        """Return the raw value behind ``index``."""
        return self._frame.iat[index.row(), index.column()]
