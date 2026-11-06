"""The application main window.

The window is a thin *controller*: it forwards user actions to the
:class:`~amazeplot.core.session.DataSession` and redraws every view when
the session notifies a change. It contains no pandas or plotting logic.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QWidget,
)

from amazeplot import __version__
from amazeplot.core.action import Action, Params
from amazeplot.core.codegen import generate_script
from amazeplot.core.errors import AmazeplotError
from amazeplot.core.examples import write_example_data
from amazeplot.core.io import (
    READABLE_EXTENSIONS,
    WRITABLE_EXTENSIONS,
    executes_code_on_read,
    load_dataframe,
    save_dataframe,
)
from amazeplot.core.operation import Operation
from amazeplot.core.registry import ActionRegistry
from amazeplot.core.session import DataSession
from amazeplot.gui.action_dialog import ActionDialog, ApplyCallback
from amazeplot.gui.actions_panel import ActionsPanel
from amazeplot.gui.data_view import DataView
from amazeplot.gui.dataframe_model import DataFrameModel
from amazeplot.gui.help_pages import build_help_pages
from amazeplot.gui.help_window import HelpWindow
from amazeplot.gui.history_panel import HistoryPanel
from amazeplot.gui.plot_panel import PlotPanel

APP_NAME = "amazeplot"
DATA_TAB = "Data"
PLOT_TAB = "Plot"
_DEFAULT_SIZE = (1280, 800)

ConfirmCallback = Callable[[str, str], bool]
"""Asks the user a yes/no question given a title and a message."""

_UNSAFE_FILE_TITLE = "Open a pickle file?"
_UNSAFE_FILE_MESSAGE = (
    "Pickle files can run any code on your computer when they are "
    "opened.\n\nOnly open {name} if you created it yourself or fully "
    "trust where it came from. Open it anyway?"
)


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
    confirm : callable, optional
        Asks the user a yes/no question, e.g. before opening a file that
        can run code. Defaults to a message box; tests pass a stub.
    """

    def __init__(
        self,
        session: DataSession,
        registry: ActionRegistry,
        parent: QWidget | None = None,
        *,
        confirm: ConfirmCallback | None = None,
    ) -> None:
        super().__init__(parent)
        self._confirm = confirm or self._ask_yes_no
        self._session = session
        self._registry = registry
        self._help_window: HelpWindow | None = None

        self.data_view = DataView()
        # Drawing is deferred while the Plot tab is hidden: see refresh().
        self._plot_stale = False

        self.plot_panel = PlotPanel()
        self.plot_panel.remove_layer_requested.connect(
            self._session.remove_layer
        )
        self.plot_panel.clear_requested.connect(self._session.clear_layers)

        self._tabs = QTabWidget()
        self._tabs.addTab(self.data_view, DATA_TAB)
        self._tabs.addTab(self.plot_panel, PLOT_TAB)
        self._tabs.currentChanged.connect(self._on_tab_changed)
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
        """Return the table model (the visible rows), mainly for tests."""
        return self.data_view.model

    def plot_is_stale(self) -> bool:
        """Return whether the figure awaits redrawing (useful for tests)."""
        return self._plot_stale

    def open_file(self, path: Path | str) -> bool:
        """Load ``path`` into the session; report errors to the user.

        Files that can run code when loaded (pickles) are only opened
        after the user confirms.

        Returns
        -------
        bool
            Whether the file was loaded.
        """
        if executes_code_on_read(path) and not self._confirm(
            _UNSAFE_FILE_TITLE,
            _UNSAFE_FILE_MESSAGE.format(name=Path(path).name),
        ):
            return False
        try:
            frame, source = load_dataframe(path)
        except AmazeplotError as exc:
            self._show_error("Cannot open file", str(exc))
            return False
        self._session.load(frame, source)
        self.data_view.go_to_row(1)
        return True

    def show_tab(self, title: str) -> None:
        """Make the central tab called ``title`` visible.

        Raises
        ------
        KeyError
            If there is no tab with that title.
        """
        for index in range(self._tabs.count()):
            if self._tabs.tabText(index) == title:
                self._tabs.setCurrentIndex(index)
                return
        raise KeyError(f"No tab called {title!r}")

    def current_tab(self) -> str:
        """Return the title of the visible central tab."""
        return self._tabs.tabText(self._tabs.currentIndex())

    def create_action_dialog(self, action: Action) -> ActionDialog:
        """Return a dialog configuring ``action`` on the current data."""
        frame = self._session.frame
        columns = [] if frame is None else frame.columns.tolist()
        return ActionDialog(
            action,
            columns,
            self._apply_callback(action),
            self,
            help_callback=lambda: self.show_help(action.key),
        )

    @property
    def help_window(self) -> HelpWindow | None:
        """Return the help window, once it has been opened."""
        return self._help_window

    def show_help(self, page_key: str | None = None) -> HelpWindow:
        """Open the help window, on ``page_key`` if given.

        The pages are built on first use, from the toolbox actions.
        """
        if self._help_window is None:
            self._help_window = HelpWindow(build_help_pages(self._registry))
        if page_key is not None:
            self._help_window.show_page(page_key)
        self._help_window.show()
        self._help_window.raise_()
        self._help_window.activateWindow()
        return self._help_window

    def open_example_data(self, directory: Path | str | None = None) -> bool:
        """Write the example table to ``directory`` and open it.

        By default the file goes to the application's data folder, so
        the exported script can load it again.

        Returns
        -------
        bool
            Whether the example data was loaded.
        """
        if directory is None:
            directory = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppLocalDataLocation
            )
        try:
            path = write_example_data(directory)
        except AmazeplotError as exc:
            self._show_error("Cannot create the example data", str(exc))
            return False
        return self.open_file(path)

    def menu_titles(self) -> list[str]:
        """Return the titles of the menu bar menus (useful for tests)."""
        return [action.text() for action in self.menuBar().actions()]

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
        self.data_view.set_frame(frame)
        self._refresh_plot()
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
            self._shape_label.setText(f"{rows:,} rows x {columns:,} columns")

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

        self._help_action = QAction(f"{APP_NAME} &Help", self)
        self._help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        self._help_action.triggered.connect(self._on_help)

        self._example_action = QAction("Open &example data", self)
        self._example_action.triggered.connect(self._on_open_example)

        self._about_action = QAction(f"&About {APP_NAME}", self)
        self._about_action.triggered.connect(self._on_about)

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

        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self._help_action)
        help_menu.addAction(self._example_action)
        help_menu.addSeparator()
        help_menu.addAction(self._about_action)

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
        is_operation = isinstance(action, Operation)
        tab = self.data_view if is_operation else self.plot_panel

        def callback(params: Params) -> None:
            self._session.perform(action, params)
            self._tabs.setCurrentWidget(tab)

        return callback

    def _refresh_plot(self) -> None:
        """Redraw the figure now if it is visible, otherwise later.

        Drawing every layer over a large table can take seconds, so a
        hidden figure is only marked stale; :meth:`_on_tab_changed`
        draws it when the Plot tab is shown.
        """
        layers = self._session.layers
        if self._tabs.currentWidget() is self.plot_panel:
            self.plot_panel.show_plot(self._session.frame, layers)
            self._plot_stale = False
        else:
            self.plot_panel.set_layers(layers)
            self._plot_stale = True

    def _on_tab_changed(self, index: int) -> None:
        if self._plot_stale and self._tabs.widget(index) is self.plot_panel:
            self._refresh_plot()

    def _on_help(self) -> None:
        self.show_help()

    def _on_open_example(self) -> None:
        self.open_example_data()

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> {__version__}<p>Transform tables with "
            "pandas and plot them with matplotlib, without writing code. "
            "Every action shows the Python code it runs.</p>"
            "<p>Press F1 for help.</p>",
        )

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

    def _ask_yes_no(self, title: str, message: str) -> bool:
        """Ask a yes/no question; the safe answer, No, is the default."""
        answer = QMessageBox.warning(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Detach from the session before the window is destroyed."""
        self._unsubscribe()
        if self._help_window is not None:
            self._help_window.close()
        super().closeEvent(event)
