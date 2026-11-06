"""Operations that add new columns computed from existing ones."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from amazeplot.core.action import Params, format_call_arguments
from amazeplot.core.operation import PANDAS_API_URL, Operation
from amazeplot.core.parameters import Parameter, ParameterKind, is_empty

CATEGORY = "Create"

NUMPY_IMPORT = "import numpy as np"
NUMPY_API_URL = "https://numpy.org/doc/stable/reference/routines.math.html"


@dataclass(frozen=True)
class ColumnFunction:
    """A numpy function offered by :data:`APPLY_FUNCTION`.

    Execution and generated code both come from ``name`` and ``kwargs``,
    so they cannot disagree.

    Attributes
    ----------
    name : str
        numpy function name, e.g. ``"angle"`` for ``np.angle``.
    suffix : str
        Appended to the column name for the default new column name.
    kwargs : Mapping
        Extra keyword arguments, e.g. ``{"deg": True}``.
    """

    name: str
    suffix: str
    kwargs: Mapping[str, Any] = field(default_factory=dict)

    def compute(self, series: pd.Series) -> Any:
        """Apply the function to ``series``."""
        return getattr(np, self.name)(series, **self.kwargs)

    def to_code(self, argument: str) -> str:
        """Return the call as source, e.g. ``np.angle(df['z'])``."""
        extra = format_call_arguments(**self.kwargs)
        return f"np.{self.name}({argument}{', ' + extra if extra else ''})"


FUNCTIONS: Mapping[str, ColumnFunction] = {
    "Absolute value (magnitude)": ColumnFunction("abs", "abs"),
    "Phase (radians)": ColumnFunction("angle", "phase"),
    "Phase (degrees)": ColumnFunction("angle", "phase_deg", {"deg": True}),
    "Real part": ColumnFunction("real", "real"),
    "Imaginary part": ColumnFunction("imag", "imag"),
    "Complex conjugate": ColumnFunction("conj", "conj"),
    "Square root": ColumnFunction("sqrt", "sqrt"),
    "Square": ColumnFunction("square", "square"),
    "Natural logarithm": ColumnFunction("log", "log"),
    "Base-10 logarithm": ColumnFunction("log10", "log10"),
    "Exponential": ColumnFunction("exp", "exp"),
}
"""Functions offered by :data:`APPLY_FUNCTION`, by the label shown."""


def new_column_name(params: Params) -> str:
    """Return the chosen name, or ``<column>_<suffix>`` when empty."""
    if not is_empty(params["new_name"]):
        return params["new_name"]
    return f"{params['column']}_{FUNCTIONS[params['function']].suffix}"


@dataclass(frozen=True)
class ApplyFunctionOperation(Operation):
    """``df.assign(**{new: np.<function>(df[column])})``."""

    @property
    def documentation_url(self) -> str:
        """Return numpy's list of mathematical functions."""
        return NUMPY_API_URL

    @property
    def code_imports(self) -> tuple[str, ...]:
        """The generated code calls numpy."""
        return (NUMPY_IMPORT,)

    def _execute(
        self, frame: pd.DataFrame, params: dict[str, Any]
    ) -> pd.DataFrame:
        function = FUNCTIONS[params["function"]]
        values = function.compute(frame[params["column"]])
        return frame.assign(**{new_column_name(params): values})

    def to_code(self, params: Params, variable: str = "df") -> str:
        """Return the equivalent ``assign`` statement."""
        function = FUNCTIONS[params["function"]]
        source = f"{variable}[{params['column']!r}]"
        name = new_column_name(params)
        return (
            f"{variable} = {variable}.assign("
            f"**{{{name!r}: {function.to_code(source)}}})"
        )


APPLY_FUNCTION = ApplyFunctionOperation(
    key="apply_function",
    example={"column": "score", "function": "Square root"},
    label="Apply a function",
    category=CATEGORY,
    description=(
        "Add a column with a function of another column: absolute "
        "value (magnitude), phase, real or imaginary part of complex "
        "numbers, square root, logarithms and more. A column with the "
        "same name is replaced."
    ),
    parameters=(
        Parameter("column", "Column", ParameterKind.COLUMN, required=True),
        Parameter(
            "function",
            "Function",
            ParameterKind.CHOICE,
            default="Absolute value (magnitude)",
            required=True,
            choices=tuple(FUNCTIONS),
        ),
        Parameter(
            "new_name",
            "New column name",
            ParameterKind.TEXT,
            help="Leave empty for e.g. value_abs or value_phase.",
        ),
    ),
)


@dataclass(frozen=True)
class CalculateColumnOperation(Operation):
    """``df.assign(**{name: df.eval(expression)})``.

    ``eval`` only computes the expression; ``assign`` sets the name.
    Assigning inside ``eval`` (``"name = ..."``) would mangle names that
    need backticks, such as names with spaces.
    """

    @property
    def documentation_url(self) -> str:
        """Return the pandas documentation page of ``eval``."""
        return PANDAS_API_URL.format("eval")

    def _execute(
        self, frame: pd.DataFrame, params: dict[str, Any]
    ) -> pd.DataFrame:
        values = frame.eval(params["expression"])
        return frame.assign(**{params["name"]: values})

    def to_code(self, params: Params, variable: str = "df") -> str:
        """Return the equivalent ``assign`` statement."""
        name = params["name"]
        values = f"{variable}.eval({params['expression']!r})"
        return f"{variable} = {variable}.assign(**{{{name!r}: {values}}})"


CALCULATE_COLUMN = CalculateColumnOperation(
    key="calculate_column",
    example={"name": "score_per_year", "expression": "score / age"},
    label="Calculate column",
    category=CATEGORY,
    description=(
        "Add a column calculated from other columns, e.g. score / age, "
        "(a + b) * 100 or abs(value). Use + - * / ** and functions such "
        "as abs, sqrt, log, exp, sin, cos, arctan2. Wrap column names "
        "containing spaces in backticks. A column with the same name is "
        "replaced."
    ),
    parameters=(
        Parameter(
            "name", "New column name", ParameterKind.TEXT, required=True
        ),
        Parameter(
            "expression",
            "Expression",
            ParameterKind.TEXT,
            required=True,
            help="E.g. score / age * 100",
        ),
    ),
)

ACTIONS = (APPLY_FUNCTION, CALCULATE_COLUMN)
