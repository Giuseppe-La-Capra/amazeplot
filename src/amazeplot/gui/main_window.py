"""The application main window.

The window is a thin *controller*: it forwards user actions to the
:class:`~amazeplot.core.session.DataSession` and redraws every view when
the session notifies a change. It contains no pandas or plotting logic.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTableView,
    QTabWidget,
    QWidget,
)

from amazeplot.core.action import Action, Params
from amazeplot.core.codegen import generate_script
from amazeplot.core.errors import AmazeplotError
from amazeplot.core.io import (
    READABLE_EXTENSIONS,
    WRITABLE_EXTENSIONS,
    load_dataframe,
    save_dataframe,
)
from amazeplot.core.operation import Operation
from amazeplot.core.plotting import PlotCall
from amazeplot.core.registry import ActionRegistry
from amazeplot.core.session import DataSession
from amazeplot.gui.action_dialog import ActionDialog, ApplyCallback
from amazeplot.gui.actions_panel import ActionsPanel
from amazeplot.gui.dataframe_model import DataFrameModel
from amazeplot.gui.history_panel import HistoryPanel
from amazeplot.gui.plot_panel import PlotPanel

APP_NAME = "amazeplot"
DATA_TAB = "Data"
PLOT_TAB = "Plot"
_DEFAULT_SIZE = (1280, 800)


def _file_filter(extensions: tuple[str, ...]) -> str:
    """Return a ``QFileDialog`` filter string for ``extensions``."""
    patterns = " ".join(f"*{extension}" for extension in extensions)
    return f"Data files ({patterns})"


class MainWindow(QMainWindow):
    """Main window: data and plot tabs, toolbox and history docked.

    Parameters
    ----------
    session : DataSession
        The session edited by this window.
    registry : ActionRegistry
        The data operations and plot calls offered in the toolbox.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self,
        session: DataSession,
        registry: ActionRegistry,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._session = session

        self._model = DataFrameModel(self)
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)

        self.plot_panel = PlotPanel()
        self.plot_panel.remove_layer_requested.connect(
            self._session.remove_layer
        )
        self.plot_panel.clear_requested.connect(self._session.clear_layers)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._table, DATA_TAB)
        self._tabs.addTab(self.plot_panel, PLOT_TAB)
        self.setCentralWidget(self._tabs)

        self.actions_panel = ActionsPanel(registry)
        self.actions_panel.action_requested.connect(self.request_action)
        self.history_panel = HistoryPanel()
        self._add_dock("Toolbox", self.actions_panel, left=True)
        self._add_dock("History", self.history_panel, left=False)

        self._shape_label = QLabel()
        self.statusBar().addPermanentWidget(self._shape_label)

        self._create_actions()
        self._create_menus()
        self.resize(*_DEFAULT_SIZE)

        self._unsubscribe = session.subscribe(self.refresh)
        self.refresh()

    # -- Public API ------------------------------------------------------

    @property
    def model(self) -> DataFrameModel:
        """Return the table model, mainly for tests."""
        return self._model

    def open_file(self, path: Path | str) -> bool:
        """Load ``path`` into the session; report errors to the user.

        Returns
        -------
        bool
            Whether the file was loaded.
        """
        try:
            frame, source = load_dataframe(path)
        except AmazeplotError as exc:
            self._show_error("Cannot open file", str(exc))
            return False
        self._session.load(frame, source)
        return True

    def current_tab(self) -> str:
        """Return the title of the visible central tab."""
        return self._tabs.tabText(self._tabs.currentIndex())

    def create_action_dialog(self, action: Action) -> ActionDialog:
        """Return a dialog configuring ``action`` on the current data."""
        frame = self._session.frame
        columns = [] if frame is None else frame.columns.tolist()
        return ActionDialog(
            action, columns, self._apply_callback(action), self
        )

    def request_action(self, action: Action) -> None:
        """Ask the user for parameters and perform ``action``."""
        if not self._session.has_data:
            self._show_error(
                action.label, "Open a data file before using the toolbox."
            )
            return
        self.create_action_dialog(action).exec()

    def refresh(self) -> None:
        """Redraw every view from the session state."""
        frame = self._session.frame
        self._model.set_frame(frame)
        self.plot_panel.show_plot(frame, self._session.layers)
        self.history_panel.set_history(
            self._session.steps, generate_script(self._session)
        )
        self._undo_action.setEnabled(self._session.can_undo)
        self._redo_action.setEnabled(self._session.can_redo)
        self._export_data_action.setEnabled(frame is not None)
        self._export_script_action.setEnabled(frame is not None)

        source = self._session.source
        self.setWindowTitle(
            f"{source.path.name} - {APP_NAME}" if source else APP_NAME
        )
        if frame is None:
            self._shape_label.setText("Open a data file to start.")
        else:
            rows, columns = frame.shape
            self._shape_label.setText(f"{rows} rows x {columns} columns")

    def status_text(self) -> str:
        """Return the text of the status bar, mainly for tests."""
        return self._shape_label.text()

    # -- Construction helpers --------------------------------------------

    def _add_dock(self, title: str, widget: QWidget, *, left: bool) -> None:
        dock = QDockWidget(title, self)
        dock.setObjectName(f"{title.lower()}_dock")
        dock.setWidget(widget)
        area = (
            Qt.DockWidgetArea.LeftDockWidgetArea
            if left
            else Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.addDockWidget(area, dock)

    def _create_actions(self) -> None:
        self._open_action = QAction("&Open...", self)
        self._open_action.setShortcut(QKeySequence.StandardKey.Open)
        self._open_action.triggered.connect(self._on_open)

        self._export_data_action = QAction("Export &data...", self)
        self._export_data_action.setShortcut(QKeySequence.StandardKey.Save)
        self._export_data_action.triggered.connect(self._on_export_data)

        self._export_script_action = QAction("Export Python &script...", self)
        self._export_script_action.triggered.connect(self._on_export_script)

        self._quit_action = QAction("&Quit", self)
        self._quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self._quit_action.triggered.connect(self.close)

        self._undo_action = QAction("&Undo", self)
        self._undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self._undo_action.triggered.connect(self._on_undo)

        self._redo_action = QAction("&Redo", self)
        self._redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self._redo_action.triggered.connect(self._on_redo)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._export_data_action)
        file_menu.addAction(self._export_script_action)
        file_menu.addSeparator()
        file_menu.addAction(self._quit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(self._undo_action)
        edit_menu.addAction(self._redo_action)

        toolbar = self.addToolBar("Main")
        toolbar.setObjectName("main_toolbar")
        toolbar.addActions(
            [self._open_action, self._undo_action, self._redo_action]
        )

    # -- Slots -----------------------------------------------------------

    def _on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open data", "", _file_filter(READABLE_EXTENSIONS)
        )
        if path:
            self.open_file(path)

    def _apply_callback(self, action: Action) -> ApplyCallback:
        """Return how ``action`` changes the session, by action type.

        Data operations add a step and show the table; plot calls add a
        layer and show the figure.
        """
        if isinstance(action, Operation):
            apply, tab = self._session.apply, self._table
        elif isinstance(action, PlotCall):
            apply, tab = self._session.add_layer, self.plot_panel
        else:
            raise TypeError(f"Unsupported action type {type(action)!r}")

        def callback(params: Params) -> None:
            apply(action, params)
            self._tabs.setCurrentWidget(tab)

        return callback

    def _on_undo(self) -> None:
        if self._session.can_undo:
            self._session.undo()

    def _on_redo(self) -> None:
        if self._session.can_redo:
            self._session.redo()

    def _on_export_data(self) -> None:
        frame = self._session.frame
        if frame is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export data", "", _file_filter(WRITABLE_EXTENSIONS)
        )
        if not path:
            return
        try:
            save_dataframe(frame, path)
        except AmazeplotError as exc:
            self._show_error("Cannot export data", str(exc))

    def _on_export_script(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Python script", "pipeline.py", "Python (*.py)"
        )
        if not path:
            return
        try:
            Path(path).write_text(
                generate_script(self._session), encoding="utf-8"
            )
        except OSError as exc:
            self._show_error("Cannot export script", str(exc))

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Detach from the session before the window is destroyed."""
        self._unsubscribe()
        super().closeEvent(event)
