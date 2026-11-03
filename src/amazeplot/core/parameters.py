"""Declarative descriptions of operation parameters.

The GUI never inspects pandas signatures directly. Every operation
declares its inputs as :class:`Parameter` objects, and the GUI builds an
editor widget for each one based on its :class:`ParameterKind`. Keeping
this description declarative means the same metadata drives validation,
the dialog, code generation and the tests.
"""

from __future__ import annotations

import ast
import enum
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from typing import Any, NoReturn

from amazeplot.core.errors import ParameterError


class ParameterKind(enum.Enum):
    """The kind of value a parameter accepts.

    The kind determines the validation rules and the editor widget the
    GUI uses for the parameter.
    """

    COLUMN = "column"
    """A single column label of the current DataFrame."""

    COLUMNS = "columns"
    """A list of column labels of the current DataFrame."""

    CHOICE = "choice"
    """One value out of :attr:`Parameter.choices`."""

    INTEGER = "integer"
    """A Python ``int``."""

    FLOAT = "float"
    """A Python ``float``."""

    BOOLEAN = "boolean"
    """A Python ``bool``."""

    TEXT = "text"
    """A free-form string, passed to pandas unchanged."""

    VALUE = "value"
    """A Python literal typed as text (``0``, ``1.5``, ``'a'``, ``None``).

    The text is parsed with :func:`ast.literal_eval`; anything that is not
    a valid literal is kept as a plain string.
    """


def is_empty(value: Any) -> bool:
    """Return whether ``value`` means "the user provided nothing".

    ``False`` and ``0`` are real values and are *not* considered empty.

    Parameters
    ----------
    value : Any
        The value to test.

    Returns
    -------
    bool
        ``True`` for ``None``, the empty string and empty lists/tuples.
    """
    if value is None:
        return True
    if isinstance(value, (str, list, tuple)):
        return len(value) == 0
    return False


def parse_literal(text: str) -> Any:
    """Parse a Python literal, falling back to the raw string.

    Parameters
    ----------
    text : str
        Text typed by the user, e.g. ``"0"``, ``"'abc'"`` or ``"abc"``.

    Returns
    -------
    Any
        The parsed literal, or ``text`` itself (stripped) when it is not
        a valid Python literal.

    Examples
    --------
    >>> parse_literal("42")
    42
    >>> parse_literal("unknown")
    'unknown'
    """
    stripped = text.strip()
    try:
        return ast.literal_eval(stripped)
    except (ValueError, SyntaxError):
        return stripped


@dataclass(frozen=True)
class Parameter:
    """Metadata describing one input of an operation.

    Attributes
    ----------
    name : str
        Keyword name. By convention this is the name of the pandas
        keyword argument the value is forwarded to.
    label : str
        Human-readable label shown in the GUI.
    kind : ParameterKind
        Kind of value, which selects the validator and editor widget.
    default : Any
        Default value. It must mirror the pandas/matplotlib default,
        because values equal to the default are omitted from the call
        and the generated code. ``None`` means "let the library decide".
    required : bool
        Whether the user must provide a non-empty value.
    choices : tuple
        Allowed values, only used when ``kind`` is ``CHOICE``.
    minimum, maximum : float or None
        Inclusive numeric bounds for ``INTEGER`` and ``FLOAT`` parameters.
    step : float or None
        Increment used by numeric editors (a GUI hint, not validated).
    help : str
        Short explanation shown as a tooltip.
    """

    name: str
    label: str
    kind: ParameterKind
    default: Any = None
    required: bool = False
    choices: tuple[Any, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    help: str = ""

    def __post_init__(self) -> None:
        """Check that the parameter definition is self-consistent."""
        if not self.name.isidentifier():
            raise ValueError(f"Invalid parameter name: {self.name!r}")
        if self.kind is ParameterKind.CHOICE and not self.choices:
            raise ValueError(f"Choice parameter {self.name!r} has no choices")

    def coerce(self, value: Any) -> Any:
        """Convert a raw editor value into the value passed to pandas.

        Parameters
        ----------
        value : Any
            Value as produced by an editor widget or by a caller.

        Returns
        -------
        Any
            The converted value. Only ``VALUE`` parameters given as text
            and ``COLUMNS`` parameters given as tuples are converted.
        """
        if self.kind is ParameterKind.VALUE and isinstance(value, str):
            return parse_literal(value) if value.strip() else None
        if self.kind is ParameterKind.COLUMNS and isinstance(value, tuple):
            return list(value)
        return value

    def validate(self, value: Any, columns: Sequence[Hashable]) -> None:
        """Validate a coerced value against this parameter definition.

        Parameters
        ----------
        value : Any
            The coerced value.
        columns : Sequence of Hashable
            Column labels of the DataFrame the operation will run on.

        Raises
        ------
        ParameterError
            If the value is missing, of the wrong type or out of range.
        """
        if is_empty(value):
            if self.required:
                raise ParameterError(f"'{self.label}' is required.")
            return
        _VALIDATORS[self.kind](self, value, columns)

    def _fail(self, reason: str) -> NoReturn:
        """Raise a :class:`ParameterError` prefixed with the label."""
        raise ParameterError(f"'{self.label}': {reason}")


def _validate_column(
    param: Parameter, value: Any, columns: Sequence[Hashable]
) -> None:
    if value not in columns:
        param._fail(f"unknown column {value!r}.")


def _validate_columns(
    param: Parameter, value: Any, columns: Sequence[Hashable]
) -> None:
    if not isinstance(value, list):
        param._fail("expected a list of columns.")
    missing = [column for column in value if column not in columns]
    if missing:
        param._fail(f"unknown column(s) {missing!r}.")


def _validate_choice(
    param: Parameter, value: Any, columns: Sequence[Hashable]
) -> None:
    if value not in param.choices:
        param._fail(f"{value!r} is not one of {list(param.choices)!r}.")


def _validate_number(
    param: Parameter, value: Any, columns: Sequence[Hashable]
) -> None:
    expected = int if param.kind is ParameterKind.INTEGER else (int, float)
    # bool is a subclass of int, but True is never a sensible row count.
    if isinstance(value, bool) or not isinstance(value, expected):
        param._fail(f"expected a number, got {value!r}.")
    if param.minimum is not None and value < param.minimum:
        param._fail(f"must be at least {param.minimum}.")
    if param.maximum is not None and value > param.maximum:
        param._fail(f"must be at most {param.maximum}.")


def _validate_boolean(
    param: Parameter, value: Any, columns: Sequence[Hashable]
) -> None:
    if not isinstance(value, bool):
        param._fail(f"expected True or False, got {value!r}.")


def _validate_text(
    param: Parameter, value: Any, columns: Sequence[Hashable]
) -> None:
    if not isinstance(value, str):
        param._fail(f"expected text, got {value!r}.")


def _validate_any(
    param: Parameter, value: Any, columns: Sequence[Hashable]
) -> None:
    """Accept any literal; pandas performs the type checking."""


_VALIDATORS = {
    ParameterKind.COLUMN: _validate_column,
    ParameterKind.COLUMNS: _validate_columns,
    ParameterKind.CHOICE: _validate_choice,
    ParameterKind.INTEGER: _validate_number,
    ParameterKind.FLOAT: _validate_number,
    ParameterKind.BOOLEAN: _validate_boolean,
    ParameterKind.TEXT: _validate_text,
    ParameterKind.VALUE: _validate_any,
}
