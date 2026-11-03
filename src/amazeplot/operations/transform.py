"""Operations that reorder or reshape the table."""

from amazeplot.core.operation import MethodOperation
from amazeplot.core.parameters import Parameter, ParameterKind

CATEGORY = "Transform"

SORT_VALUES = MethodOperation(
    key="sort_values",
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
    label="Reset index",
    category=CATEGORY,
    description="Replace the row index with 0, 1, 2, ...",
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
    label="Transpose",
    category=CATEGORY,
    description="Swap rows and columns.",
    method="transpose",
)

OPERATIONS = (SORT_VALUES, SET_INDEX, RESET_INDEX, TRANSPOSE)
