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
        editor.set_checked([3, "a"])
    assert editor.value() == ["a", 3]
