"""Heatmap, hexagonal density values and colour bar."""

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from amazeplot.core.errors import PlotError
from amazeplot.core.session import DataSession
from amazeplot.operations.decorate import COLORBAR
from amazeplot.operations.plot import HEATMAP, HEXBIN, LINE, SCATTER


@pytest.fixture
def grid_frame():
    """Two rows per (i, j) cell, one cell missing, numeric axes."""
    rows = [
        (i, j, float(10 * i + j + offset))
        for i in range(3)
        for j in range(4)
        for offset in (0, 2)
        if (i, j) != (2, 3)
    ]
    return pd.DataFrame(rows, columns=["i", "j", "level"])


def _draw(call, frame, params):
    axes = Figure().add_subplot()
    resolved = call.resolve_params(params, frame.columns.tolist())
    call.draw(frame, resolved, axes)
    return axes


def test_heatmap_grid_values(grid_frame):
    axes = _draw(HEATMAP, grid_frame, {"x": "j", "y": "i", "values": "level"})
    mesh = axes.collections[0]
    values = np.ma.filled(mesh.get_array(), np.nan).reshape(3, 4)
    assert values[0, 0] == 1.0  # mean of 0 and 2
    assert values[1, 2] == 13.0  # mean of 12 and 14
    assert np.isnan(values[2, 3])  # no data: empty cell
    assert len(axes.figure.axes) == 1  # the colour bar is its own layer


def test_heatmap_combine_and_no_colour_bar(grid_frame):
    params = {"x": "j", "y": "i", "values": "level", "aggfunc": "max"}
    axes = _draw(HEATMAP, grid_frame, params)
    assert axes.collections[0].get_array().max() == 24.0  # cell (2, 2)


def test_heatmap_with_text_categories(people):
    axes = _draw(HEATMAP, people, {"x": "city", "y": "name", "values": "age"})
    labels = [label.get_text() for label in axes.get_xticklabels()]
    assert set(labels) == {"Oslo", "Rome"}


def test_heatmap_code_reproduces_the_drawing(grid_frame):
    params = {"x": "j", "y": "i", "values": "level", "cmap": "magma"}
    resolved = HEATMAP.resolve_params(params, grid_frame.columns.tolist())
    code = HEATMAP.to_code(resolved)
    assert code.splitlines()[0] == (
        "grid = df.pivot_table(index='i', columns='j', values='level', "
        "aggfunc='mean')"
    )
    expected = _draw(HEATMAP, grid_frame, params)
    actual = Figure().add_subplot()
    exec(code, {"df": grid_frame, "ax": actual, "fig": actual.figure})
    np.testing.assert_array_equal(
        actual.collections[0].get_array(), expected.collections[0].get_array()
    )
    assert actual.collections[0].get_cmap().name == "magma"


def test_hexbin_values_column(grid_frame):
    params = {"x": "j", "y": "i", "C": "level", "gridsize": 3}
    resolved = HEXBIN.resolve_params(params, grid_frame.columns.tolist())
    assert "C=df['level']" in HEXBIN.to_code(resolved)
    axes = _draw(HEXBIN, grid_frame, params)
    assert axes.collections[0].get_array().max() > 1  # means, not counts


def test_colour_bar_needs_a_colour_coded_layer(people):
    session = DataSession()
    session.load(people)
    session.add_layer(LINE, {"y": "score"})
    with pytest.raises(PlotError, match="colour-coded layer"):
        session.add_layer(COLORBAR, {"label": "Score"})

    session.add_layer(SCATTER, {"x": "age", "y": "score", "c": "score"})
    layer = session.add_layer(COLORBAR, {"label": "Score"})
    assert layer.to_code() == (
        "fig.colorbar(ax.collections[-1], ax=ax, label='Score')"
    )


def _labels(session):
    return [layer.label for layer in session.layers]


def test_heatmap_adds_a_separate_colour_bar_layer(grid_frame):
    session = DataSession()
    session.load(grid_frame)
    heatmap = session.add_layer(
        HEATMAP, {"x": "j", "y": "i", "values": "level"}
    )
    assert heatmap.call is HEATMAP
    assert _labels(session) == ["Heatmap", "Colour bar"]
    assert session.layers[1].to_code() == (
        "fig.colorbar(ax.collections[-1], ax=ax, label='level')"
    )
    assert "colorbar" not in heatmap.to_code()  # not drawn by the heatmap

    session.remove_layer(1)  # The colour bar can go on its own...
    assert _labels(session) == ["Heatmap"]
    session.undo()
    session.undo()  # ...and adding both was a single undo step.
    assert _labels(session) == []


def test_colour_bar_layer_can_be_switched_off(grid_frame):
    session = DataSession()
    session.load(grid_frame)
    params = {"x": "j", "y": "i", "values": "level", "colorbar": False}
    session.add_layer(HEATMAP, params)
    assert _labels(session) == ["Heatmap"]


def test_scatter_adds_a_colour_bar_only_when_colour_coded(people):
    session = DataSession()
    session.load(people)
    session.add_layer(SCATTER, {"x": "age", "y": "score", "colorbar": True})
    assert _labels(session) == ["Scatter"]  # one colour: nothing to show
    session.add_layer(
        SCATTER, {"x": "age", "y": "score", "c": "score", "colorbar": True}
    )
    assert _labels(session)[-2:] == ["Scatter", "Colour bar"]
    assert "colorbar" not in session.layers[-2].to_code()


def test_hexbin_colour_bar_labels(grid_frame):
    session = DataSession()
    session.load(grid_frame)
    session.add_layer(HEXBIN, {"x": "j", "y": "i", "gridsize": 3})
    session.add_layer(HEXBIN, {"x": "j", "y": "i", "C": "level"})
    bars = [layer for layer in session.layers if layer.call is COLORBAR]
    assert [bar.params["label"] for bar in bars] == ["Count", "level"]
