"""Operations that reorder or reshape the table."""

from __future__ import annotations

from collections.abc import Hashable
from dataclasses import dataclass
from typing import Any

import pandas as pd

from amazeplot.core.action import Params
from amazeplot.core.operation import PANDAS_API_URL, MethodOperation, Operation
from amazeplot.core.parameters import Parameter, ParameterKind

CATEGORY = "Transform"

SORT_VALUES = MethodOperation(
    key="sort_values",
    example={"by": ["age"], "ascending": False},
    label="Sort rows",
    category=CATEGORY,
    description="Sort the rows by one or more columns.",
    parameters=(
        Parameter(
            name="by",
            label="Sort by",
            kind=ParameterKind.COLUMNS,
            required=True,
        ),
        Parameter(
            name="ascending",
            label="Ascending",
            kind=ParameterKind.BOOLEAN,
            default=True,
        ),
        Parameter(
            name="na_position",
            label="Missing values",
            kind=ParameterKind.CHOICE,
            default="last",
            choices=("last", "first"),
        ),
    ),
    method="sort_values",
)

SET_INDEX = MethodOperation(
    key="set_index",
    example={"keys": ["name"]},
    label="Set index",
    category=CATEGORY,
    description="Use one or more columns as the row index.",
    parameters=(
        Parameter(
            name="keys",
            label="Columns",
            kind=ParameterKind.COLUMNS,
            required=True,
        ),
        Parameter(
            name="drop",
            label="Remove from columns",
            kind=ParameterKind.BOOLEAN,
            default=True,
        ),
    ),
    method="set_index",
)

RESET_INDEX = MethodOperation(
    key="reset_index",
    example={"drop": True},
    label="Reset index",
    category=CATEGORY,
    description=(
        "Replace the row index with 0, 1, 2, ... The old index becomes "
        "ordinary columns (one per level for multi-level row labels)."
    ),
    parameters=(
        Parameter(
            name="drop",
            label="Discard old index",
            kind=ParameterKind.BOOLEAN,
            default=False,
            help="Unticked: the old index becomes a column.",
        ),
    ),
    method="reset_index",
)

TRANSPOSE = MethodOperation(
    key="transpose",
    example={},
    label="Transpose",
    category=CATEGORY,
    description="Swap rows and columns.",
    method="transpose",
)


def flat_label(label: Hashable, sep: str) -> Hashable:
    """Join the levels of a multi-level label; keep other labels as-is.

    This is the exact rule the generated code spells out inline, so the
    GUI and the script produce the same names.
    """
    if isinstance(label, tuple):
        return sep.join(map(str, label))
    return label


@dataclass(frozen=True)
class FlattenColumnsOperation(Operation):
    """Replace multi-level column names by single strings.

    ``('price', 'mean')`` becomes ``'price_mean'`` with separator ``_``.
    A custom class because the generated code is a list comprehension
    over ``df.columns``, not a single method call with fixed arguments.
    """

    @property
    def documentation_url(self) -> str:
        """Return the pandas documentation page of ``set_axis``."""
        return PANDAS_API_URL.format("set_axis")

    def _execute(
        self, frame: pd.DataFrame, params: dict[str, Any]
    ) -> pd.DataFrame:
        labels = [flat_label(label, params["sep"]) for label in frame.columns]
        return frame.set_axis(labels, axis=1)

    def to_code(self, params: Params, variable: str = "df") -> str:
        """Return the equivalent ``set_axis`` statement."""
        sep = params["sep"]
        return (
            f"{variable} = {variable}.set_axis("
            f"[{sep!r}.join(map(str, c)) if isinstance(c, tuple) else c "
            f"for c in {variable}.columns], axis=1)"
        )


FLATTEN_COLUMNS = FlattenColumnsOperation(
    key="flatten_columns",
    example={"sep": "_"},
    label="Flatten column names",
    category=CATEGORY,
    description=(
        "Turn multi-level column names, such as those made by a pivot "
        "table, into simple names by joining the levels. Single-level "
        "names are kept. For multi-level row labels, use Reset index."
    ),
    parameters=(
        Parameter(
            name="sep",
            label="Join levels with",
            kind=ParameterKind.TEXT,
            default="_",
            required=True,
            help="Text placed between the levels, e.g. _ or a space.",
        ),
    ),
)

ACTIONS = (SORT_VALUES, SET_INDEX, RESET_INDEX, FLATTEN_COLUMNS, TRANSPOSE)
