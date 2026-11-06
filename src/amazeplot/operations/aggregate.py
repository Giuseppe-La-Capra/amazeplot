"""Operations that summarise the data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from amazeplot.core.action import Params, format_call_arguments
from amazeplot.core.operation import (
    PANDAS_API_URL,
    MethodOperation,
    Operation,
)
from amazeplot.core.parameters import Parameter, ParameterKind, is_empty
from amazeplot.operations._common import AGGREGATIONS, SUBSET

CATEGORY = "Aggregate"


@dataclass(frozen=True)
class GroupByOperation(Operation):
    """``df.groupby(by, as_index=False)[columns].agg(func)``.

    This needs a custom class because the pandas expression chains
    three calls, which :class:`MethodOperation` cannot describe.
    """

    @property
    def documentation_url(self) -> str:
        """Return the pandas documentation page of ``groupby``."""
        return PANDAS_API_URL.format("groupby")

    def _execute(
        self, frame: pd.DataFrame, params: dict[str, Any]
    ) -> pd.DataFrame:
        grouped = frame.groupby(params["by"], as_index=False)
        if not is_empty(params["columns"]):
            grouped = grouped[params["columns"]]
        return grouped.agg(params["func"])

    def to_code(self, params: Params, variable: str = "df") -> str:
        """Return the equivalent ``groupby`` statement."""
        arguments = format_call_arguments(params["by"], as_index=False)
        code = f"{variable} = {variable}.groupby({arguments})"
        if not is_empty(params["columns"]):
            code += f"[{params['columns']!r}]"
        return code + f".agg({params['func']!r})"


GROUPBY = GroupByOperation(
    key="groupby",
    example={"by": ["city"], "columns": ["score"], "func": "mean"},
    label="Group and aggregate",
    category=CATEGORY,
    description=(
        "Split the rows into groups sharing the same key values and "
        "summarise every group with one function."
    ),
    parameters=(
        Parameter(
            name="by",
            label="Group by",
            kind=ParameterKind.COLUMNS,
            required=True,
        ),
        Parameter(
            name="columns",
            label="Aggregate columns",
            kind=ParameterKind.COLUMNS,
            help="Leave empty to aggregate every other column.",
        ),
        Parameter(
            name="func",
            label="Function",
            kind=ParameterKind.CHOICE,
            default="mean",
            required=True,
            choices=AGGREGATIONS,
        ),
    ),
)

DESCRIBE = MethodOperation(
    key="describe",
    example={},
    label="Summary statistics",
    category=CATEGORY,
    description="Count, mean, standard deviation and quantiles.",
    method="describe",
)

VALUE_COUNTS = MethodOperation(
    key="value_counts",
    example={"subset": ["city"]},
    label="Count unique rows",
    category=CATEGORY,
    description="Count how often each distinct combination occurs.",
    parameters=(
        SUBSET,
        Parameter(
            name="normalize",
            label="As proportions",
            kind=ParameterKind.BOOLEAN,
            default=False,
        ),
        Parameter(
            name="dropna",
            label="Ignore missing values",
            kind=ParameterKind.BOOLEAN,
            default=True,
        ),
    ),
    method="value_counts",
    then="reset_index",
)

PIVOT_TABLE = MethodOperation(
    key="pivot_table",
    example={"index": ["city"], "values": ["score"]},
    label="Pivot table",
    category=CATEGORY,
    description="Spreadsheet-style pivot table.",
    parameters=(
        Parameter(
            name="index",
            label="Rows",
            kind=ParameterKind.COLUMNS,
            required=True,
        ),
        Parameter(
            name="columns",
            label="Columns",
            kind=ParameterKind.COLUMNS,
        ),
        Parameter(
            name="values",
            label="Values",
            kind=ParameterKind.COLUMNS,
            help="Leave empty to aggregate every other column.",
        ),
        Parameter(
            name="aggfunc",
            label="Function",
            kind=ParameterKind.CHOICE,
            default="mean",
            choices=AGGREGATIONS,
        ),
    ),
    method="pivot_table",
    then="reset_index",
)

CORR = MethodOperation(
    key="corr",
    example={"numeric_only": True},
    label="Correlation matrix",
    category=CATEGORY,
    description="Pairwise correlation of columns.",
    parameters=(
        Parameter(
            name="method",
            label="Method",
            kind=ParameterKind.CHOICE,
            default="pearson",
            choices=("pearson", "kendall", "spearman"),
        ),
        Parameter(
            name="numeric_only",
            label="Numeric columns only",
            kind=ParameterKind.BOOLEAN,
            default=False,
        ),
    ),
    method="corr",
)

ACTIONS = (GROUPBY, DESCRIBE, VALUE_COUNTS, PIVOT_TABLE, CORR)
