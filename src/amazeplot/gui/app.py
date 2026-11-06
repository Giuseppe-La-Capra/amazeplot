"""Application entry point: wires the core objects to the main window."""

from __future__ import annotations

import logging
import sys
import traceback
from collections.abc import Sequence
from types import TracebackType

from PySide6.QtWidgets import QApplication, QMessageBox, QWidget

from amazeplot import __version__
from amazeplot.core.session import DataSession
from amazeplot.gui.main_window import APP_NAME, MainWindow
from amazeplot.operations import build_default_registry

logger = logging.getLogger(__name__)


def install_exception_hook(parent: QWidget) -> None:
    """Log unexpected exceptions and show them instead of crashing.

    Expected, user-caused failures are handled where they occur. Anything
    reaching this hook is a bug, so the full traceback is logged.
    """

    def hook(
        exc_type: type[BaseException],
        exc: BaseException,
        tb: TracebackType | None,
    ) -> None:
        details = "".join(traceback.format_exception(exc_type, exc, tb))
        logger.error("Unexpected error:\n%s", details)
        QMessageBox.critical(
            parent,
            "Unexpected error",
            f"{exc_type.__name__}: {exc}\n\nSee the log for details.",
        )

    sys.excepthook = hook


def main(argv: Sequence[str] | None = None) -> int:
    """Start the GUI and return the process exit code.

    Parameters
    ----------
    argv : sequence of str, optional
        Command-line arguments; defaults to ``sys.argv``. An optional
        first positional argument is a data file to open on start-up.
    """
    arguments = list(sys.argv if argv is None else argv)
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )

    app = QApplication(arguments)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)

    window = MainWindow(DataSession(), build_default_registry())
    install_exception_hook(window)
    window.show()
    if len(arguments) > 1:
        window.open_file(arguments[1])
    return app.exec()
