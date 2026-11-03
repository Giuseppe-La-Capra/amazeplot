"""Panel showing the figure built from the session's plot layers."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT,
)
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from amazeplot.core.errors import PlotError
from amazeplot.core.plotting import Layer, render_layers

_ERROR_STYLE = "color: #c62828;"
_EMPTY_HINT = (
    "Add a layer from the Plot category of the toolbox, then decorate "
    "it with titles, labels or a legend."
)
_SIDEBAR_WIDTH = 220


class PlotPanel(QWidget):
    """Interactive matplotlib figure plus the list of its layers.

    The panel only *displays* layers; it asks the main window to change
    them through :attr:`remove_layer_requested` and
    :attr:`clear_requested`.
    """

    remove_layer_requested = Signal(int)
    clear_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._figure = Figure(layout="constrained")
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._axes: Axes | None = None

        self._message = QLabel(_EMPTY_HINT)
        self._message.setWordWrap(True)

        self._layers = QListWidget()
        self._layers.currentRowChanged.connect(self._update_buttons)
        self._remove_button = QPushButton("Remove layer")
        self._remove_button.clicked.connect(self.remove_selected_layer)
        self._clear_button = QPushButton("Clear plot")
        self._clear_button.clicked.connect(self.clear_requested)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_figure_area())
        splitter.addWidget(self._build_sidebar())
        splitter.setStretchFactor(0, 1)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self._update_buttons()

    # -- Public API ------------------------------------------------------

    @property
    def figure(self) -> Figure:
        """Return the displayed figure (e.g. to save it)."""
        return self._figure

    def show_plot(
        self, frame: pd.DataFrame | None, layers: Sequence[Layer]
    ) -> None:
        """Redraw the figure from ``layers`` using ``frame``.

        A layer that fails (for instance after its column was dropped)
        is reported below the figure; the layers before it stay drawn.
        """
        self._figure.clear()
        self._axes = None
        message, is_error = _EMPTY_HINT, False
        if frame is not None and layers:
            self._axes = self._figure.add_subplot()
            message = ""
            try:
                render_layers(layers, frame, self._axes)
            except PlotError as exc:
                message, is_error = str(exc), True
        self._show_message(message, is_error=is_error)
        self._set_layers(layers)
        self._canvas.draw_idle()

    def axes(self) -> Axes | None:
        """Return the axes currently drawn on, if any (for tests)."""
        return self._axes

    def message_text(self) -> str:
        """Return the hint or error shown under the figure."""
        return self._message.text() if not self._message.isHidden() else ""

    def layer_labels(self) -> list[str]:
        """Return the texts of the listed layers."""
        return [
            self._layers.item(row).text()
            for row in range(self._layers.count())
        ]

    def select_layer(self, row: int) -> None:
        """Select the layer at ``row``."""
        self._layers.setCurrentRow(row)

    def remove_selected_layer(self) -> None:
        """Ask for the selected layer to be removed, if any."""
        row = self._layers.currentRow()
        if row >= 0:
            self.remove_layer_requested.emit(row)

    # -- Construction helpers --------------------------------------------

    def _build_figure_area(self) -> QWidget:
        area = QWidget()
        layout = QVBoxLayout(area)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(NavigationToolbar2QT(self._canvas, area))
        layout.addWidget(self._canvas, stretch=1)
        layout.addWidget(self._message)
        return area

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setMaximumWidth(_SIDEBAR_WIDTH)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Layers (drawn top to bottom)"))
        layout.addWidget(self._layers)
        layout.addWidget(self._remove_button)
        layout.addWidget(self._clear_button)
        return sidebar

    # -- Slots and helpers -----------------------------------------------

    def _set_layers(self, layers: Sequence[Layer]) -> None:
        self._layers.clear()
        for number, layer in enumerate(layers, start=1):
            item = QListWidgetItem(f"{number}. {layer.label}")
            item.setToolTip(layer.to_code())
            self._layers.addItem(item)
        self._update_buttons()

    def _show_message(self, text: str, *, is_error: bool) -> None:
        self._message.setText(text)
        self._message.setStyleSheet(_ERROR_STYLE if is_error else "")
        self._message.setHidden(not text)

    def _update_buttons(self) -> None:
        self._remove_button.setEnabled(self._layers.currentRow() >= 0)
        self._clear_button.setEnabled(self._layers.count() > 0)
