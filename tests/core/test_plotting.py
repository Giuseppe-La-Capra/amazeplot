import pandas as pd
import pytest
from matplotlib.figure import Figure

from amazeplot.core.errors import PlotError
from amazeplot.core.parameters import Parameter, ParameterKind
from amazeplot.core.plotting import (
    AxesCall,
    ColumnRef,
    Layer,
    render_argument,
    render_layers,
    resolve_argument,
)

X = Parameter("x", "X", ParameterKind.COLUMN, required=False)
Y = Parameter("y", "Y", ParameterKind.COLUMN, required=True)
ALPHA = Parameter("alpha", "Alpha", ParameterKind.FLOAT)
LINE = AxesCall(
    "line",
    "Line",
    "Plot",
    "",
    (X, Y, ALPHA),
    method="plot",
    positional=("x", "y"),
)


@pytest.fixture
def axes():
    return Figure().add_subplot()


def test_column_ref(people):
    ref = ColumnRef("age", dropna=True)
    assert ref.to_code("df") == "df['age'].dropna()"
    assert len(ref.resolve(people)) == 4


def test_render_and_resolve_nested_lists(people):
    value = [ColumnRef("age"), ColumnRef("score")]
    assert render_argument(value, "df") == "[df['age'], df['score']]"
    resolved = resolve_argument(value, people)
    assert [series.name for series in resolved] == ["age", "score"]
    assert render_argument("text", "df") == "'text'"


def test_unknown_axes_method_is_rejected():
    with pytest.raises(ValueError, match="no method"):
        AxesCall("k", "K", "C", "", method="not_a_method")


def test_unknown_positional_parameter_is_rejected():
    with pytest.raises(KeyError):
        AxesCall("k", "K", "C", "", (Y,), method="plot", positional=("z",))


def test_empty_positional_arguments_are_skipped():
    assert LINE.to_code({"x": None, "y": "age"}) == "ax.plot(df['age'])"


def test_keyword_arguments_and_defaults():
    code = LINE.to_code({"x": "name", "y": "age", "alpha": 0.5})
    assert code == "ax.plot(df['name'], df['age'], alpha=0.5)"


def test_draw_adds_artists(people, axes):
    LINE.draw(people, {"x": None, "y": "score", "alpha": None}, axes)
    assert len(axes.get_lines()) == 1


def test_draw_failure_becomes_plot_error(people, axes):
    with pytest.raises(PlotError, match="Line failed"):
        LINE.draw(people, {"x": None, "y": "missing", "alpha": None}, axes)


def test_check_uses_a_scratch_figure(people):
    LINE.check(people, {"x": None, "y": "score", "alpha": None})
    with pytest.raises(PlotError):
        LINE.check(people, {"x": None, "y": "missing", "alpha": None})


def test_render_layers_in_order(people, axes):
    layers = [
        Layer(LINE, {"x": None, "y": "score", "alpha": None}),
        Layer(LINE, {"x": None, "y": "age", "alpha": None}),
    ]
    render_layers(layers, people, axes)
    lines = axes.get_lines()
    assert [line.get_ydata()[0] for line in lines] == [7.5, 31]


def test_layer_code(people):
    layer = Layer(LINE, {"x": None, "y": "score", "alpha": None})
    assert layer.label == "Line"
    assert layer.to_code("data") == "ax.plot(data['score'])"


def test_dataframe_is_not_mutated(people, axes):
    before = people.copy()
    LINE.draw(people, {"x": "age", "y": "score", "alpha": 0.3}, axes)
    pd.testing.assert_frame_equal(people, before)
