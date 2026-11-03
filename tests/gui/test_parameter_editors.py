import pytest

from amazeplot.core.parameters import Parameter, ParameterKind
from amazeplot.gui.parameter_editors import EDITOR_CLASSES, create_editor

COLUMNS = ["a", "b", 3]


def test_every_kind_has_an_editor():
    assert set(EDITOR_CLASSES) == set(ParameterKind)


@pytest.mark.parametrize(
    ("parameter", "expected"),
    [
        (Parameter("c", "C", ParameterKind.COLUMN), None),
        (Parameter("c", "C", ParameterKind.COLUMN, required=True), "a"),
        (Parameter("c", "C", ParameterKind.COLUMNS, default=["b"]), ["b"]),
        (
            Parameter(
                "k",
                "K",
                ParameterKind.CHOICE,
                default=False,
                choices=("first", False),
            ),
            False,
        ),
        (Parameter("n", "N", ParameterKind.INTEGER, default=5), 5),
        (Parameter("x", "X", ParameterKind.FLOAT, default=0.5), 0.5),
        (Parameter("b", "B", ParameterKind.BOOLEAN, default=True), True),
        (Parameter("t", "T", ParameterKind.TEXT), ""),
        (Parameter("n", "N", ParameterKind.INTEGER), None),
        (Parameter("x", "X", ParameterKind.FLOAT, minimum=0.0), None),
        (Parameter("n", "N", ParameterKind.INTEGER, required=True), 0),
        (
            Parameter("m", "M", ParameterKind.CHOICE, choices=(None, "o")),
            None,
        ),
    ],
    ids=lambda value: getattr(value, "kind", value),
)
def test_editor_starts_at_default(qtbot, parameter, expected):
    editor = create_editor(parameter, COLUMNS)
    qtbot.addWidget(editor)
    assert editor.value() == expected


def test_columns_editor_keeps_non_string_labels(qtbot):
    editor = create_editor(Parameter("c", "C", ParameterKind.COLUMNS), COLUMNS)
    qtbot.addWidget(editor)
    with qtbot.waitSignal(editor.value_changed):
        editor.set_value([3, "a"])
    assert editor.value() == ["a", 3]


def test_optional_number_can_be_set_and_reset(qtbot):
    editor = create_editor(
        Parameter("alpha", "A", ParameterKind.FLOAT, minimum=0.0, step=0.1),
        COLUMNS,
    )
    qtbot.addWidget(editor)
    editor.set_value(0.5)
    assert editor.value() == 0.5
    editor.set_value(0.0)
    assert editor.value() == 0.0
    editor.set_value(None)
    assert editor.value() is None
