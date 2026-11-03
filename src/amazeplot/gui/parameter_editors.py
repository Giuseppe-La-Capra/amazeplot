"""Editor widgets for operation parameters.

Every :class:`~amazeplot.core.parameters.ParameterKind` maps to exactly
one :class:`ParameterEditor` subclass. Adding a new kind therefore means
adding one class here and one entry in :data:`EDITOR_CLASSES`; the
operation dialog needs no change.
"""

from __future__ import annotations

from collections.abc import Hashable, Sequence
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QWidget,
)

from amazeplot.core.parameters import Parameter, ParameterKind

_INT_LIMIT = 2**31 - 1
_NO_SELECTION_TEXT = "(none)"
_COLUMNS_LIST_HEIGHT = 140


class ParameterEditor(QWidget):
    """Base class of the widgets that edit one parameter.

    Subclasses build their inner widget in :meth:`_build`, return the
    current value from :meth:`value` and emit :attr:`value_changed`
    whenever the user edits it.

    Parameters
    ----------
    parameter : Parameter
        The parameter being edited.
    columns : Sequence of Hashable
        Column labels of the current DataFrame.
    parent : QWidget, optional
        Parent widget.
    """

    value_changed = Signal()

    def __init__(
        self,
        parameter: Parameter,
        columns: Sequence[Hashable],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.parameter = parameter
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._build(columns))
        self.setToolTip(parameter.help)

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        """Create, initialise and connect the inner widget."""
        raise NotImplementedError

    def value(self) -> Any:
        """Return the value currently entered by the user."""
        raise NotImplementedError


class ColumnEditor(ParameterEditor):
    """Drop-down list with one column label."""

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        self._combo = QComboBox()
        if not self.parameter.required:
            self._combo.addItem(_NO_SELECTION_TEXT, None)
        for column in columns:
            self._combo.addItem(str(column), column)
        index = self._combo.findData(self.parameter.default)
        self._combo.setCurrentIndex(max(index, 0))
        self._combo.currentIndexChanged.connect(self.value_changed)
        return self._combo

    def value(self) -> Hashable | None:
        """Return the selected column label, or ``None``."""
        return self._combo.currentData()


class ColumnsEditor(ParameterEditor):
    """Checkable list of column labels, preserving the frame's order."""

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        self._list = QListWidget()
        self._list.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self._list.setMaximumHeight(_COLUMNS_LIST_HEIGHT)
        selected = self.parameter.default or []
        for column in columns:
            item = QListWidgetItem(str(column))
            item.setData(Qt.ItemDataRole.UserRole, column)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = column in selected
            item.setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )
            self._list.addItem(item)
        self._list.itemChanged.connect(self.value_changed)
        return self._list

    def value(self) -> list[Hashable]:
        """Return the checked column labels."""
        return [
            item.data(Qt.ItemDataRole.UserRole)
            for item in map(self._list.item, range(self._list.count()))
            if item.checkState() == Qt.CheckState.Checked
        ]

    def set_checked(self, columns: Sequence[Hashable]) -> None:
        """Check exactly the given columns (useful for tests)."""
        for row in range(self._list.count()):
            item = self._list.item(row)
            checked = item.data(Qt.ItemDataRole.UserRole) in columns
            item.setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )


class ChoiceEditor(ParameterEditor):
    """Drop-down list with the parameter's choices."""

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        self._combo = QComboBox()
        for choice in self.parameter.choices:
            text = _NO_SELECTION_TEXT if choice is None else str(choice)
            self._combo.addItem(text, choice)
        index = self._combo.findData(self.parameter.default)
        self._combo.setCurrentIndex(max(index, 0))
        self._combo.currentIndexChanged.connect(self.value_changed)
        return self._combo

    def value(self) -> Any:
        """Return the selected choice."""
        return self.parameter.choices[self._combo.currentIndex()]


class IntegerEditor(ParameterEditor):
    """Spin box for whole numbers."""

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        self._spin = QSpinBox()
        low, high = _bounds(self.parameter, -_INT_LIMIT, _INT_LIMIT)
        self._spin.setRange(int(low), int(high))
        self._spin.setValue(int(self.parameter.default or 0))
        self._spin.valueChanged.connect(self.value_changed)
        return self._spin

    def value(self) -> int:
        """Return the entered integer."""
        return self._spin.value()


class FloatEditor(ParameterEditor):
    """Spin box for decimal numbers."""

    _DECIMALS = 6

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        self._spin = QDoubleSpinBox()
        self._spin.setDecimals(self._DECIMALS)
        self._spin.setRange(*_bounds(self.parameter, -1e12, 1e12))
        self._spin.setValue(float(self.parameter.default or 0.0))
        self._spin.valueChanged.connect(self.value_changed)
        return self._spin

    def value(self) -> float:
        """Return the entered number."""
        return self._spin.value()


class BooleanEditor(ParameterEditor):
    """Check box."""

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        self._check = QCheckBox()
        self._check.setChecked(bool(self.parameter.default))
        self._check.toggled.connect(self.value_changed)
        return self._check

    def value(self) -> bool:
        """Return whether the box is ticked."""
        return self._check.isChecked()


class TextEditor(ParameterEditor):
    """Single-line text field, used for ``TEXT`` and ``VALUE`` kinds."""

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        self._line = QLineEdit()
        if self.parameter.default is not None:
            self._line.setText(str(self.parameter.default))
        self._line.setPlaceholderText(self.parameter.help)
        self._line.textChanged.connect(self.value_changed)
        return self._line

    def value(self) -> str:
        """Return the entered text; parsing happens in the core."""
        return self._line.text()

    def set_text(self, text: str) -> None:
        """Replace the entered text (useful for tests)."""
        self._line.setText(text)


EDITOR_CLASSES: dict[ParameterKind, type[ParameterEditor]] = {
    ParameterKind.COLUMN: ColumnEditor,
    ParameterKind.COLUMNS: ColumnsEditor,
    ParameterKind.CHOICE: ChoiceEditor,
    ParameterKind.INTEGER: IntegerEditor,
    ParameterKind.FLOAT: FloatEditor,
    ParameterKind.BOOLEAN: BooleanEditor,
    ParameterKind.TEXT: TextEditor,
    ParameterKind.VALUE: TextEditor,
}
"""The editor class used for each parameter kind."""


def create_editor(
    parameter: Parameter,
    columns: Sequence[Hashable],
    parent: QWidget | None = None,
) -> ParameterEditor:
    """Return a new editor widget suited to ``parameter``."""
    return EDITOR_CLASSES[parameter.kind](parameter, columns, parent)


def _bounds(
    parameter: Parameter, low: float, high: float
) -> tuple[float, float]:
    """Return the parameter bounds, falling back to ``low``/``high``."""
    minimum = low if parameter.minimum is None else parameter.minimum
    maximum = high if parameter.maximum is None else parameter.maximum
    return minimum, maximum
