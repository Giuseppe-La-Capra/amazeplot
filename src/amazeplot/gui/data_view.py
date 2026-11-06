"""The Data tab: navigation bar, table showing one slice, info panel.

Only the rows inside the current :class:`RowWindow` are given to the
table model, so a DataFrame of any length stays responsive. The bar
lets the user pick the first row, the page size and move page by page.
Below the table, an :class:`InfoPanel` describes the column and the row
of the selected cell, computed over the whole DataFrame.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from amazeplot.core.summary import Sections, column_summary, row_summary
from amazeplot.gui.dataframe_model import DataFrameModel
from amazeplot.gui.info_panel import InfoPanel
from amazeplot.gui.row_window import DEFAULT_PAGE_SIZE, PAGE_SIZES, RowWindow

_TABLE_TO_PANEL_RATIO = (3, 1)
_MAX_COLUMN_WIDTH = 320  # Pixels; long values stay readable in the panel.
_FIT_SAMPLE_ROWS = 100  # Rows Qt measures when fitting column widths.
# Fitting is per column, so wide tables only fit the first ones; the
# info panel shows any value in full.
_FIT_MAX_COLUMNS = 50
_START_TOOLTIP = (
    "Position of the first row shown, counting from 1. The labels on "
    "the left of the table are the DataFrame's index."
)


class DataView(QWidget):
    """Navigation bar, a table showing one page of rows, info panel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._frame: pd.DataFrame | None = None
        self._window = RowWindow()
        # Column statistics scan the whole frame: compute each once.
        self._column_cache: dict[int, Sections] = {}

        self.model = DataFrameModel(self)
        self._table = QTableView()
        self._table.setModel(self.model)
        self._table.setAlternatingRowColors(True)
        header = self._table.horizontalHeader()
        header.setMaximumSectionSize(_MAX_COLUMN_WIDTH)
        header.setResizeContentsPrecision(_FIT_SAMPLE_ROWS)
        self._table.selectionModel().currentChanged.connect(
            self._on_current_changed
        )
        self.info_panel = InfoPanel()

        self._start = QSpinBox()
        self._start.setKeyboardTracking(False)  # Jump on Enter, not per key.
        self._start.setToolTip(_START_TOOLTIP)
        self._start.valueChanged.connect(self.go_to_row)

        self._page_size = QComboBox()
        for size in PAGE_SIZES:
            self._page_size.addItem(f"{size:,}", size)
        self._page_size.setCurrentIndex(PAGE_SIZES.index(DEFAULT_PAGE_SIZE))
        self._page_size.currentIndexChanged.connect(self._on_page_size)

        self._previous = QPushButton("◀ Previous")
        self._previous.clicked.connect(self.previous_page)
        self._next = QPushButton("Next ▶")
        self._next.clicked.connect(self.next_page)
        self._range = QLabel()

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Rows from"))
        bar.addWidget(self._start)
        bar.addWidget(QLabel("Rows per page"))
        bar.addWidget(self._page_size)
        bar.addWidget(self._previous)
        bar.addWidget(self._next)
        bar.addWidget(self._range, stretch=1)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._table)
        splitter.addWidget(self.info_panel)
        for index, stretch in enumerate(_TABLE_TO_PANEL_RATIO):
            splitter.setStretchFactor(index, stretch)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(bar)
        layout.addWidget(splitter)
        self._show(self._window)

    # -- Public API ------------------------------------------------------

    @property
    def window(self) -> RowWindow:
        """Return the rows currently shown."""
        return self._window

    def set_frame(self, frame: pd.DataFrame | None) -> None:
        """Show ``frame``, keeping the current position when possible."""
        if frame is not self._frame:
            self._column_cache.clear()
        columns_changed = not _same_columns(self._frame, frame)
        self._frame = frame
        self._show(self._window)
        if columns_changed:
            # Only when the columns change, so manual widths survive
            # paging and data steps that keep the columns.
            self._fit_column_widths()

    def go_to_row(self, row: int) -> None:
        """Show rows starting at position ``row`` (counting from 1)."""
        self._show(RowWindow(max(row - 1, 0), self._window.size))

    def set_page_size(self, size: int) -> None:
        """Show ``size`` rows at once, from the same first row.

        Raises
        ------
        ValueError
            If ``size`` is not one of :data:`PAGE_SIZES`.
        """
        if size not in PAGE_SIZES:
            raise ValueError(f"Page size must be one of {PAGE_SIZES}")
        self._show(RowWindow(self._window.start, size))

    def previous_page(self) -> None:
        """Show the previous page of rows."""
        self._show(self._window.previous())

    def next_page(self) -> None:
        """Show the next page of rows."""
        self._show(self._window.next(self._total()))

    def select_cell(self, row: int, column: int) -> None:
        """Select the cell at ``row`` (on the current page) and ``column``.

        Both are 0-based positions; the info panel then describes them.
        """
        self._table.setCurrentIndex(self.model.index(row, column))

    def column_width(self, column: int) -> int:
        """Return the width of ``column`` in pixels (useful for tests)."""
        return self._table.columnWidth(column)

    def set_column_width(self, column: int, width: int) -> None:
        """Set the width of ``column``, as dragging its border does."""
        self._table.setColumnWidth(column, width)

    def range_text(self) -> str:
        """Return the "Showing rows ..." text (useful for tests)."""
        return self._range.text()

    # -- Helpers ---------------------------------------------------------

    def _total(self) -> int:
        return 0 if self._frame is None else len(self._frame.index)

    def _show(self, window: RowWindow) -> None:
        """Give the table only the rows of ``window`` and sync the bar."""
        total = self._total()
        self._window = window.clamped(total)
        if self._frame is None:
            self.model.set_frame(None)
        else:
            first, stop = self._window.start, self._window.stop(total)
            self.model.set_frame(self._frame.iloc[first:stop])
        # Resetting the model drops the selection without a signal.
        self.info_panel.clear()
        self._sync_bar(total)

    def _sync_bar(self, total: int) -> None:
        has_data = self._frame is not None
        # Setting the widgets must not re-trigger navigation.
        for widget in (self._start, self._page_size):
            widget.blockSignals(True)
        self._start.setRange(1, max(total, 1))
        self._start.setValue(self._window.start + 1)
        self._page_size.setCurrentIndex(
            self._page_size.findData(self._window.size)
        )
        for widget in (self._start, self._page_size):
            widget.blockSignals(False)
        for widget in (self._start, self._page_size):
            widget.setEnabled(has_data)
        self._previous.setEnabled(self._window.has_previous())
        self._next.setEnabled(self._window.has_next(total))
        self._range.setText(self._window.describe(total) if has_data else "")

    def _fit_column_widths(self) -> None:
        for column in range(min(self.model.columnCount(), _FIT_MAX_COLUMNS)):
            self._table.resizeColumnToContents(column)

    def _on_current_changed(
        self, current: QModelIndex, previous: object
    ) -> None:
        """Describe the column and row of the newly selected cell."""
        if self._frame is None or not current.isValid():
            self.info_panel.clear()
            return
        column = current.column()
        if column not in self._column_cache:
            self._column_cache[column] = column_summary(self._frame, column)
        row = self._window.start + current.row()
        self.info_panel.show_details(
            self._column_cache[column], row_summary(self._frame, row)
        )

    def _on_page_size(self, index: int) -> None:
        self.set_page_size(self._page_size.itemData(index))


def _same_columns(old: pd.DataFrame | None, new: pd.DataFrame | None) -> bool:
    """Return whether two frames (or ``None``) have identical columns."""
    if old is None or new is None:
        return old is new
    return old.columns.equals(new.columns)
