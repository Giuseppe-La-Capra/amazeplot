"""Parameter definitions shared by several operation modules."""

from amazeplot.core.parameters import Parameter, ParameterKind

ROW_COUNT = Parameter(
    name="n",
    label="Rows",
    kind=ParameterKind.INTEGER,
    default=5,
    minimum=0,
    help="Number of rows to keep.",
)

SUBSET = Parameter(
    name="subset",
    label="Columns",
    kind=ParameterKind.COLUMNS,
    help="Only consider these columns (default: all columns).",
)

AGGREGATIONS = (
    "sum",
    "mean",
    "median",
    "min",
    "max",
    "count",
    "nunique",
    "std",
    "var",
    "first",
    "last",
)
"""Aggregation function names accepted by pandas ``agg``."""
