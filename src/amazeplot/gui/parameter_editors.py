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

from amazeplot.core.formatting import format_label
from amazeplot.core.parameters import Parameter, ParameterKind

_INT_LIMIT = 2**31 - 1
_FLOAT_LIMIT = 1e12
_NO_SELECTION_TEXT = "(none)"
_LIBRARY_DEFAULT_TEXT = "(default)"
_COLUMNS_LIST_HEIGHT = 140


class ParameterEditor(QWidget):
    """Base class of the widgets that edit one parameter.

    Subclasses build their inner widget in :meth:`_build`, return the
    current value from :meth:`value`, accept a new one in
    :meth:`set_value`, and emit :attr:`value_changed` whenever the value
    changes.

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

    def set_value(self, value: Any) -> None:
        """Show ``value`` in the editor, as if the user entered it."""
        raise NotImplementedError


class ColumnEditor(ParameterEditor):
    """Drop-down list with one column label."""

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        self._combo = QComboBox()
        if not self.parameter.required:
            self._combo.addItem(_NO_SELECTION_TEXT, None)
        for column in columns:
            self._combo.addItem(format_label(column), column)
        index = self._combo.findData(self.parameter.default)
        self._combo.setCurrentIndex(max(index, 0))
        self._combo.currentIndexChanged.connect(self.value_changed)
        return self._combo

    def value(self) -> Hashable | None:
        """Return the selected column label, or ``None``."""
        return self._combo.currentData()

    def set_value(self, value: Hashable | None) -> None:
        """Select the column ``value`` (``None`` for no column)."""
        self._combo.setCurrentIndex(self._combo.findData(value))


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
            item = QListWidgetItem(format_label(column))
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

    def set_value(self, value: Sequence[Hashable] | None) -> None:
        """Check exactly the columns in ``value``."""
        columns = value or []
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
            text = _LIBRARY_DEFAULT_TEXT if choice is None else str(choice)
            self._combo.addItem(text, choice)
        index = self._combo.findData(self.parameter.default)
        self._combo.setCurrentIndex(max(index, 0))
        self._combo.currentIndexChanged.connect(self.value_changed)
        return self._combo

    def value(self) -> Any:
        """Return the selected choice."""
        return self.parameter.choices[self._combo.currentIndex()]

    def set_value(self, value: Any) -> None:
        """Select the choice equal to ``value``."""
        self._combo.setCurrentIndex(self.parameter.choices.index(value))


class _NumberEditor(ParameterEditor):
    """Shared logic of the integer and float spin boxes.

    An optional parameter whose default is ``None`` gets one extra step
    below its minimum, displayed as "(default)", which maps back to
    ``None`` so matplotlib or pandas choose the value.
    """

    _number_type: type[int] | type[float] = float

    def _configure(
        self, spin: QSpinBox | QDoubleSpinBox, limit: float
    ) -> None:
        """Set range, step and initial value of ``spin``."""
        self._spin = spin
        param = self.parameter
        cast = self._number_type
        low, high = (cast(bound) for bound in _bounds(param, -limit, limit))
        step = cast(param.step if param.step is not None else 1)
        self._optional = param.default is None and not param.required
        if self._optional:
            low -= step
            spin.setSpecialValueText(_LIBRARY_DEFAULT_TEXT)
        spin.setRange(low, high)
        spin.setSingleStep(step)
        if self._optional:
            spin.setValue(low)
        elif param.default is not None:
            spin.setValue(cast(param.default))
        spin.valueChanged.connect(self.value_changed)

    def value(self) -> int | float | None:
        """Return the entered number, or ``None`` for "(default)"."""
        current = self._spin.value()
        if self._optional and current == self._spin.minimum():
            return None
        return current

    def set_value(self, value: float | None) -> None:
        """Enter ``value``; ``None`` selects "(default)"."""
        if value is None:
            self._spin.setValue(self._spin.minimum())
        else:
            self._spin.setValue(value)


class IntegerEditor(_NumberEditor):
    """Spin box for whole numbers."""

    _number_type = int

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        spin = QSpinBox()
        self._configure(spin, _INT_LIMIT)
        return spin


class FloatEditor(_NumberEditor):
    """Spin box for decimal numbers."""

    _DECIMALS = 3

    def _build(self, columns: Sequence[Hashable]) -> QWidget:
        spin = QDoubleSpinBox()
        spin.setDecimals(self._DECIMALS)
        self._configure(spin, _FLOAT_LIMIT)
        return spin


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

    def set_value(self, value: bool) -> None:
        """Tick the box when ``value`` is true."""
        self._check.setChecked(bool(value))


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

    def set_value(self, value: Any) -> None:
        """Replace the entered text with ``value`` (``None`` clears)."""
        self._line.setText("" if value is None else str(value))


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
