"""Dialog that collects the parameters of one action."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Mapping, Sequence
from typing import Any

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from amazeplot.core.action import Action
from amazeplot.core.errors import ActionError
from amazeplot.gui.parameter_editors import ParameterEditor, create_editor

ApplyCallback = Callable[[Mapping[str, Any]], object]
"""Called with the entered values; raises ``ActionError`` on failure."""

_ERROR_STYLE = "color: #c62828;"
_REQUIRED_MARKER = " *"


class ActionDialog(QDialog):
    """Form generated from :attr:`Action.parameters`.

    While the user types, the dialog shows the pandas or matplotlib code
    that will run. Pressing *OK* calls ``apply_callback``; if it raises
    :class:`ActionError` the message is shown and the dialog stays open
    so the user can fix the input.

    Parameters
    ----------
    action : Action
        The data operation or plot call to configure.
    columns : Sequence of Hashable
        Column labels of the current DataFrame.
    apply_callback : callable
        Receives the entered values when the user confirms.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self,
        action: Action,
        columns: Sequence[Hashable],
        apply_callback: ApplyCallback,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._action = action
        self._columns = list(columns)
        self._apply_callback = apply_callback
        self._editors: dict[str, ParameterEditor] = {}

        self.setWindowTitle(action.label)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        description = QLabel(action.description)
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        for param in action.parameters:
            editor = create_editor(param, self._columns, self)
            editor.value_changed.connect(self._update_preview)
            marker = _REQUIRED_MARKER if param.required else ""
            form.addRow(param.label + marker, editor)
            self._editors[param.name] = editor
        layout.addLayout(form)

        self._preview = QLabel()
        self._preview.setWordWrap(True)
        self._preview.setFont(
            QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        )
        layout.addWidget(self._preview)

        self._error = QLabel()
        self._error.setWordWrap(True)
        self._error.setStyleSheet(_ERROR_STYLE)
        self._error.hide()
        layout.addWidget(self._error)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accepted)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._update_preview()

    def editor(self, name: str) -> ParameterEditor:
        """Return the editor of the parameter called ``name``."""
        return self._editors[name]

    def values(self) -> dict[str, Any]:
        """Return the current value of every editor."""
        return {name: ed.value() for name, ed in self._editors.items()}

    def set_values(self, values: Mapping[str, Any]) -> None:
        """Fill in editors from ``values`` (e.g. to repeat an action)."""
        for name, value in values.items():
            self._editors[name].set_value(value)

    def confirm(self) -> None:
        """Behave as if the user pressed *OK*."""
        self._on_accepted()

    def preview_text(self) -> str:
        """Return the code preview currently displayed."""
        return self._preview.text()

    def error_text(self) -> str:
        """Return the error message currently displayed, if any."""
        return self._error.text() if self._error.isVisibleTo(self) else ""

    def _update_preview(self) -> None:
        """Show the code that would run, or why it cannot run yet."""
        try:
            resolved = self._action.resolve_params(
                self.values(), self._columns
            )
        except ActionError as exc:
            self._preview.setText(str(exc))
            return
        self._preview.setText(self._action.to_code(resolved))

    def _on_accepted(self) -> None:
        try:
            self._apply_callback(self.values())
        except ActionError as exc:
            self._error.setText(str(exc))
            self._error.show()
            return
        self.accept()
