"""The Data tab: a row-navigation bar above a table showing one slice.

Only the rows inside the current :class:`RowWindow` are given to the
table model, so a DataFrame of any length stays responsive. The bar
lets the user pick the first row, the page size and move page by page.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from amazeplot.gui.dataframe_model import DataFrameModel
from amazeplot.gui.row_window import DEFAULT_PAGE_SIZE, PAGE_SIZES, RowWindow

_START_TOOLTIP = (
    "Position of the first row shown, counting from 1. The labels on "
    "the left of the table are the DataFrame's index."
)


class DataView(QWidget):
    """Row-navigation bar plus a table showing one page of rows."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._frame: pd.DataFrame | None = None
        self._window = RowWindow()

        self.model = DataFrameModel(self)
        self._table = QTableView()
        self._table.setModel(self.model)
        self._table.setAlternatingRowColors(True)

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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(bar)
        layout.addWidget(self._table)
        self._show(self._window)

    # -- Public API ------------------------------------------------------

    @property
    def window(self) -> RowWindow:
        """Return the rows currently shown."""
        return self._window

    def set_frame(self, frame: pd.DataFrame | None) -> None:
        """Show ``frame``, keeping the current position when possible."""
        self._frame = frame
        self._show(self._window)

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

    def _on_page_size(self, index: int) -> None:
        self.set_page_size(self._page_size.itemData(index))
