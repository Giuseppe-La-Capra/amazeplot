import pandas as pd
import pytest

from amazeplot.core.errors import OperationError, ParameterError
from amazeplot.core.operation import MethodOperation, format_call_arguments
from amazeplot.core.parameters import Parameter, ParameterKind

HOW = Parameter(
    "how", "How", ParameterKind.CHOICE, default="any", choices=("any", "all")
)
DROPNA = MethodOperation(
    key="dropna",
    label="Drop missing",
    category="Test",
    description="",
    parameters=(HOW,),
    method="dropna",
)


def test_format_call_arguments():
    assert format_call_arguments(["a"], n=1) == "['a'], n=1"


def test_unknown_method_is_rejected():
    with pytest.raises(ValueError, match="no method"):
        MethodOperation("k", "K", "C", "", method="not_a_method")


def test_duplicate_parameter_names_are_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        MethodOperation("k", "K", "C", "", (HOW, HOW), method="dropna")


def test_default_values_are_omitted_from_code():
    assert DROPNA.to_code({"how": "any"}) == "df = df.dropna()"
    assert DROPNA.to_code({"how": "all"}) == "df = df.dropna(how='all')"


def test_custom_variable_name():
    assert DROPNA.to_code({"how": "any"}, "data") == "data = data.dropna()"


def test_apply_does_not_mutate_input(people):
    before = people.copy()
    DROPNA.apply(people, {})
    pd.testing.assert_frame_equal(people, before)


def test_unknown_parameter_is_rejected(people):
    with pytest.raises(ParameterError, match="unknown parameter"):
        DROPNA.apply(people, {"nope": 1})


def test_invalid_parameter_raises_parameter_error(people):
    with pytest.raises(ParameterError):
        DROPNA.apply(people, {"how": "sometimes"})


def test_pandas_failure_becomes_operation_error(people):
    query = MethodOperation(
        "query",
        "Filter",
        "C",
        "",
        (Parameter("expr", "Expr", ParameterKind.TEXT, required=True),),
        method="query",
    )
    with pytest.raises(OperationError, match="Filter failed"):
        query.apply(people, {"expr": "age >>> 3"})


def test_non_dataframe_result_is_a_programming_error(people):
    # count() returns a Series for any column types on every pandas.
    broken = MethodOperation("count", "Count", "C", "", method="count")
    with pytest.raises(TypeError, match="expected DataFrame"):
        broken.apply(people, {})
