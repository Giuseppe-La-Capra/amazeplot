import pytest

from amazeplot.core.errors import ParameterError
from amazeplot.core.parameters import (
    Parameter,
    ParameterKind,
    is_empty,
    parse_literal,
)

COLUMNS = ["a", "b"]


@pytest.mark.parametrize("value", [None, "", [], ()])
def test_is_empty_true(value):
    assert is_empty(value)


@pytest.mark.parametrize("value", [0, False, "x", ["a"], 0.0])
def test_is_empty_false(value):
    assert not is_empty(value)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("42", 42),
        ("1.5", 1.5),
        ("'a'", "a"),
        ("None", None),
        ("True", True),
        (" plain text ", "plain text"),
    ],
)
def test_parse_literal(text, expected):
    assert parse_literal(text) == expected


def test_choice_without_choices_is_rejected():
    with pytest.raises(ValueError, match="no choices"):
        Parameter("how", "How", ParameterKind.CHOICE)


def test_invalid_name_is_rejected():
    with pytest.raises(ValueError, match="Invalid parameter name"):
        Parameter("not valid", "Label", ParameterKind.TEXT)


def test_required_parameter_rejects_empty_value():
    param = Parameter("x", "X", ParameterKind.TEXT, required=True)
    with pytest.raises(ParameterError, match="required"):
        param.validate("", COLUMNS)


def test_optional_parameter_accepts_empty_value():
    Parameter("x", "X", ParameterKind.COLUMNS).validate(None, COLUMNS)


def test_unknown_column_is_rejected():
    param = Parameter("col", "Col", ParameterKind.COLUMN)
    with pytest.raises(ParameterError, match="unknown column"):
        param.validate("zzz", COLUMNS)


def test_unknown_columns_are_rejected():
    param = Parameter("cols", "Cols", ParameterKind.COLUMNS)
    with pytest.raises(ParameterError, match="zzz"):
        param.validate(["a", "zzz"], COLUMNS)


def test_choice_validation():
    param = Parameter("how", "How", ParameterKind.CHOICE, choices=("a",))
    param.validate("a", COLUMNS)
    with pytest.raises(ParameterError):
        param.validate("b", COLUMNS)


@pytest.mark.parametrize("value", [-1, 11, True, "3"])
def test_integer_validation_rejects(value):
    param = Parameter("n", "N", ParameterKind.INTEGER, minimum=0, maximum=10)
    with pytest.raises(ParameterError):
        param.validate(value, COLUMNS)


def test_value_parameter_coerces_text():
    param = Parameter("v", "V", ParameterKind.VALUE)
    assert param.coerce("3") == 3
    assert param.coerce("  ") is None
