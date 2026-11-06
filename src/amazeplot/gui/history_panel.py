"""Panel listing the applied steps and the equivalent Python script."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from amazeplot.core.session import Step


class HistoryPanel(QWidget):
    """Read-only view of the session history and generated code."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._steps = QListWidget()
        self._code = QPlainTextEdit()
        self._code.setReadOnly(True)
        self._code.setFont(
            QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Applied steps"))
        layout.addWidget(self._steps)
        layout.addWidget(QLabel("Python code"))
        layout.addWidget(self._code)

    def set_history(self, steps: Sequence[Step], script: str) -> None:
        """Display ``steps`` and the full generated ``script``."""
        self._steps.clear()
        for number, step in enumerate(steps, start=1):
            item = QListWidgetItem(f"{number}. {step.label}")
            item.setToolTip(step.to_code())
            self._steps.addItem(item)
        self._code.setPlainText(script)

    def step_labels(self) -> list[str]:
        """Return the texts of the listed steps."""
        return [
            self._steps.item(row).text() for row in range(self._steps.count())
        ]

    def script(self) -> str:
        """Return the displayed script."""
        return self._code.toPlainText()
