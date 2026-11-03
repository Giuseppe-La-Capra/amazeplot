"""Contract tests run against every built-in plot call.

When you add a plot call, add an entry to ``EXAMPLES``: the tests then
check that it draws, and that its generated code draws exactly the same
artists as the GUI.
"""

import numpy as np
import pandas as pd
import pytest
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from amazeplot.core.plotting import PlotCall
from amazeplot.operations import build_default_registry

PLOT_CALLS = [
    action
    for action in build_default_registry()
    if isinstance(action, PlotCall)
]

EXAMPLES = {
    "plot_line": {"x": "age", "y": "score", "marker": "o", "label": "s"},
    "plot_scatter": {"x": "age", "y": "score", "c": "score", "s": 40.0},
    "plot_bar": {"x": "name", "height": "score", "color": "tab:red"},
    "plot_barh": {"y": "name", "width": "score", "height": 0.5},
    "plot_hist": {"x": ["age", "score"], "bins": 5},
    "plot_box": {"x": ["age", "score"], "showmeans": True},
    "plot_pie": {"x": "score", "labels": "name", "autopct": "%1.0f%%"},
    "plot_area": {"x": "score", "y1": "age", "alpha": 0.3},
    "plot_step": {"x": "score", "y": "age", "where": "mid"},
    "plot_stem": {"heads": "score"},
    "plot_errorbar": {"x": "score", "y": "age", "yerr": "score"},
    "plot_hexbin": {"x": "age", "y": "score", "gridsize": 5},
    "plot_heatmap": {"cmap": "viridis", "aspect": "auto"},
    "set_title": {"label": "People", "loc": "left"},
    "set_xlabel": {"xlabel": "Age"},
    "set_ylabel": {"ylabel": "Score"},
    "legend": {"loc": "upper left", "title": "Legend"},
    "grid": {"visible": True, "axis": "y"},
    "set_xscale": {"value": "log"},
    "set_yscale": {"value": "symlog"},
    "set_xlim": {"left": 0.0, "right": 10.0},
    "set_ylim": {"bottom": -1.0},
    "axhline": {"y": 7.0, "linestyle": "--"},
    "axvline": {"x": 2.0, "color": "black"},
    "text": {"x": 1.0, "y": 2.0, "s": "Note"},
    "tick_params": {"axis": "x", "labelrotation": 45.0},
}


def _round(values) -> list:
    """Return array-like ``values`` as a comparable nested list."""
    array = np.ma.filled(np.ma.asarray(values, dtype=float), np.nan)
    return np.round(array, 9).tolist()


def _fingerprint(axes: Axes) -> str:
    """Summarise everything drawn on ``axes`` as comparable text."""
    parts = [
        axes.get_title(),
        axes.get_title("left"),
        axes.get_xlabel(),
        axes.get_ylabel(),
        axes.get_xscale(),
        axes.get_yscale(),
        _round(axes.get_xlim()),
        _round(axes.get_ylim()),
    ]
    for child in axes.get_children():
        parts.append(type(child).__name__)
        if hasattr(child, "get_xydata"):
            parts.append(_round(child.get_xydata()))
        if hasattr(child, "get_offsets"):
            parts.append(_round(child.get_offsets()))
        if hasattr(child, "get_text"):
            parts.append(child.get_text())
        if hasattr(child, "get_bbox") and hasattr(child, "get_width"):
            parts.append(_round(child.get_bbox().bounds))
    for axis in (axes.xaxis, axes.yaxis):
        # Pie charts remove every tick, so check before indexing.
        for tick in axis.get_major_ticks()[:1]:
            parts.append(
                (tick.gridline.get_visible(), tick.label1.get_rotation())
            )
    legend = axes.get_legend()
    if legend is not None:
        parts.append([text.get_text() for text in legend.get_texts()])
    return repr(parts)


def _draw_layer(call: PlotCall, frame: pd.DataFrame, params) -> Axes:
    """Draw a reference line then ``call``, like a real figure would."""
    axes = Figure().add_subplot()
    axes.plot([1, 2], [3, 4], label="reference")
    call.draw(frame, params, axes)
    return axes


def test_every_plot_call_has_an_example():
    assert {call.key for call in PLOT_CALLS} == set(EXAMPLES)


@pytest.mark.parametrize("call", PLOT_CALLS, ids=lambda call: call.key)
def test_example_changes_the_axes(call: PlotCall, people):
    # Guards the contract test below against passing vacuously.
    resolved = call.resolve_params(EXAMPLES[call.key], people.columns.tolist())
    untouched = Figure().add_subplot()
    untouched.plot([1, 2], [3, 4], label="reference")
    drawn = _draw_layer(call, people, resolved)
    assert _fingerprint(drawn) != _fingerprint(untouched)


@pytest.mark.parametrize("call", PLOT_CALLS, ids=lambda call: call.key)
def test_generated_code_draws_the_same(call: PlotCall, people):
    resolved = call.resolve_params(EXAMPLES[call.key], people.columns.tolist())
    expected = _draw_layer(call, people, resolved)

    actual = Figure().add_subplot()
    actual.plot([1, 2], [3, 4], label="reference")
    exec(call.to_code(resolved), {"df": people.copy(), "ax": actual})

    assert _fingerprint(actual) == _fingerprint(expected)


@pytest.mark.parametrize("call", PLOT_CALLS, ids=lambda call: call.key)
def test_plot_call_does_not_mutate_input(call: PlotCall, people):
    before = people.copy()
    resolved = call.resolve_params(EXAMPLES[call.key], people.columns.tolist())
    _draw_layer(call, people, resolved)
    pd.testing.assert_frame_equal(people, before)
