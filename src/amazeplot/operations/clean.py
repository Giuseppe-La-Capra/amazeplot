"""Operations that fix missing, duplicated or mistyped data."""

from typing import Any

from amazeplot.core.action import Params
from amazeplot.core.operation import MethodOperation
from amazeplot.core.parameters import Parameter, ParameterKind, is_empty
from amazeplot.operations._common import SUBSET

CATEGORY = "Clean"

DTYPES = (
    "int64",
    "Int64",
    "float64",
    "bool",
    "string",
    "category",
    "datetime64[ns]",
    "object",
)
"""Target types offered by :data:`ASTYPE`."""

DROPNA = MethodOperation(
    key="dropna",
    example={"how": "any", "subset": ["age"]},
    label="Drop missing values",
    category=CATEGORY,
    description="Remove rows that contain missing values.",
    parameters=(
        Parameter(
            name="how",
            label="Drop when",
            kind=ParameterKind.CHOICE,
            default="any",
            choices=("any", "all"),
            help="'any': a value is missing; 'all': every value is.",
        ),
        SUBSET,
    ),
    method="dropna",
)


def _fillna_kwargs(params: Params) -> dict[str, Any]:
    """Fill one column when a column is chosen, otherwise every column."""
    value = params["value"]
    column = params["column"]
    return {"value": value if is_empty(column) else {column: value}}


FILLNA = MethodOperation(
    key="fillna",
    example={"value": "0", "column": "age"},
    label="Fill missing values",
    category=CATEGORY,
    description="Replace missing values with a constant.",
    parameters=(
        Parameter(
            name="value",
            label="Value",
            kind=ParameterKind.VALUE,
            required=True,
            help="A Python literal: 0, 1.5, 'text', True ...",
        ),
        Parameter(
            name="column",
            label="Only in column",
            kind=ParameterKind.COLUMN,
            help="Leave empty to fill every column.",
        ),
    ),
    method="fillna",
    kwargs_builder=_fillna_kwargs,
)

DROP_DUPLICATES = MethodOperation(
    key="drop_duplicates",
    example={"keep": False},
    label="Drop duplicates",
    category=CATEGORY,
    description="Remove duplicated rows.",
    parameters=(
        SUBSET,
        Parameter(
            name="keep",
            label="Keep",
            kind=ParameterKind.CHOICE,
            default="first",
            choices=("first", "last", False),
            help="Which duplicate to keep; False drops all of them.",
        ),
    ),
    method="drop_duplicates",
)


def _rename_kwargs(params: Params) -> dict[str, Any]:
    return {"columns": {params["column"]: params["new_name"]}}


RENAME_COLUMN = MethodOperation(
    key="rename_column",
    example={"column": "age", "new_name": "years"},
    label="Rename column",
    category=CATEGORY,
    description="Give a column a new name.",
    parameters=(
        Parameter(
            name="column",
            label="Column",
            kind=ParameterKind.COLUMN,
            required=True,
        ),
        Parameter(
            name="new_name",
            label="New name",
            kind=ParameterKind.TEXT,
            required=True,
        ),
    ),
    method="rename",
    kwargs_builder=_rename_kwargs,
)


def _astype_kwargs(params: Params) -> dict[str, Any]:
    return {"dtype": {params["column"]: params["dtype"]}}


ASTYPE = MethodOperation(
    key="astype",
    example={"column": "score", "dtype": "string"},
    label="Change column type",
    category=CATEGORY,
    description="Convert a column to another data type.",
    parameters=(
        Parameter(
            name="column",
            label="Column",
            kind=ParameterKind.COLUMN,
            required=True,
        ),
        Parameter(
            name="dtype",
            label="New type",
            kind=ParameterKind.CHOICE,
            default="float64",
            required=True,
            choices=DTYPES,
        ),
    ),
    method="astype",
    kwargs_builder=_astype_kwargs,
)

REPLACE = MethodOperation(
    key="replace",
    example={"to_replace": "'Rome'", "value": "'Roma'"},
    label="Replace values",
    category=CATEGORY,
    description="Replace every occurrence of a value with another.",
    parameters=(
        Parameter(
            name="to_replace",
            label="Find",
            kind=ParameterKind.VALUE,
            required=True,
            help="A Python literal: 0, 1.5, 'text', True ...",
        ),
        Parameter(
            name="value",
            label="Replace with",
            kind=ParameterKind.VALUE,
            required=True,
            help="A Python literal: 0, 1.5, 'text', True ...",
        ),
    ),
    method="replace",
)

ACTIONS = (
    DROPNA,
    FILLNA,
    DROP_DUPLICATES,
    RENAME_COLUMN,
    ASTYPE,
    REPLACE,
)
