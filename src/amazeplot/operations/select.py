"""Operations that select a subset of rows or columns."""

from amazeplot.core.operation import MethodOperation
from amazeplot.core.parameters import Parameter, ParameterKind
from amazeplot.operations._common import ROW_COUNT

CATEGORY = "Select"

HEAD = MethodOperation(
    key="head",
    label="First rows",
    category=CATEGORY,
    description="Keep only the first n rows.",
    parameters=(ROW_COUNT,),
    method="head",
)

TAIL = MethodOperation(
    key="tail",
    label="Last rows",
    category=CATEGORY,
    description="Keep only the last n rows.",
    parameters=(ROW_COUNT,),
    method="tail",
)

QUERY = MethodOperation(
    key="query",
    label="Filter rows",
    category=CATEGORY,
    description=(
        "Keep the rows matching a boolean expression, e.g. "
        "age > 30 and city == 'Rome'. Wrap column names containing "
        "spaces in backticks."
    ),
    parameters=(
        Parameter(
            name="expr",
            label="Expression",
            kind=ParameterKind.TEXT,
            required=True,
            help="A pandas query expression.",
        ),
    ),
    method="query",
)

SELECT_COLUMNS = MethodOperation(
    key="select_columns",
    label="Select columns",
    category=CATEGORY,
    description="Keep only the chosen columns, in their original order.",
    parameters=(
        Parameter(
            name="items",
            label="Columns",
            kind=ParameterKind.COLUMNS,
            required=True,
        ),
    ),
    method="filter",
)

DROP_COLUMNS = MethodOperation(
    key="drop_columns",
    label="Drop columns",
    category=CATEGORY,
    description="Remove the chosen columns.",
    parameters=(
        Parameter(
            name="columns",
            label="Columns",
            kind=ParameterKind.COLUMNS,
            required=True,
        ),
    ),
    method="drop",
)

_LARGEST_PARAMETERS = (
    Parameter(
        name="n",
        label="Rows",
        kind=ParameterKind.INTEGER,
        default=5,
        required=True,
        minimum=0,
    ),
    Parameter(
        name="columns",
        label="Order by",
        kind=ParameterKind.COLUMNS,
        required=True,
        help="Numeric columns used for ordering.",
    ),
)

NLARGEST = MethodOperation(
    key="nlargest",
    label="Largest values",
    category=CATEGORY,
    description="Keep the n rows with the largest values.",
    parameters=_LARGEST_PARAMETERS,
    method="nlargest",
)

NSMALLEST = MethodOperation(
    key="nsmallest",
    label="Smallest values",
    category=CATEGORY,
    description="Keep the n rows with the smallest values.",
    parameters=_LARGEST_PARAMETERS,
    method="nsmallest",
)

ACTIONS = (
    HEAD,
    TAIL,
    QUERY,
    SELECT_COLUMNS,
    DROP_COLUMNS,
    NLARGEST,
    NSMALLEST,
)
