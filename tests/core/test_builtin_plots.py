"""Contract tests run against every built-in plot call.

Every plot call declares an ``example`` in the catalogue. The tests run
it to check that it draws, and that its generated code draws exactly the
same artists as the GUI.
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


def _round(values) -> list:
    """Return array-like ``values`` as a comparable nested list."""
    array = np.ma.filled(np.ma.asarray(values, dtype=float), np.nan)
    return np.round(array, 9).tolist()


def _fingerprint(axes: Axes) -> str:
    """Summarise everything drawn on ``axes`` as comparable text."""
    parts = [
        len(axes.figure.axes),  # A colour bar adds axes to the figure.
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
        if getattr(child, "get_array", None) and child.get_array() is not None:
            parts.append(_round(child.get_array()))  # Colour data.
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


def _reference_axes() -> Axes:
    """Return fresh axes with a labelled, colour-coded reference layer.

    Decorations such as the legend and the colour bar build on it, like
    they would on earlier layers of a real figure.
    """
    axes = Figure().add_subplot()
    axes.scatter([1, 2], [3, 4], c=[1.0, 2.0], label="reference")
    return axes


def _draw_layer(call: PlotCall, frame: pd.DataFrame, params) -> Axes:
    """Draw the reference then ``call``, like a real figure would."""
    axes = _reference_axes()
    call.draw(frame, params, axes)
    return axes


def test_every_plot_call_has_an_example():
    assert [call.key for call in PLOT_CALLS if call.example is None] == []


@pytest.mark.parametrize("call", PLOT_CALLS, ids=lambda call: call.key)
def test_example_changes_the_axes(call: PlotCall, people):
    # Guards the contract test below against passing vacuously.
    resolved = call.resolve_params(call.example, people.columns.tolist())
    untouched = _reference_axes()
    drawn = _draw_layer(call, people, resolved)
    assert _fingerprint(drawn) != _fingerprint(untouched)


@pytest.mark.parametrize("call", PLOT_CALLS, ids=lambda call: call.key)
def test_generated_code_draws_the_same(call: PlotCall, people):
    resolved = call.resolve_params(call.example, people.columns.tolist())
    expected = _draw_layer(call, people, resolved)

    actual = _reference_axes()
    namespace = {"df": people.copy(), "ax": actual, "fig": actual.figure}
    exec("\n".join(call.code_imports), namespace)
    exec(call.to_code(resolved), namespace)

    assert _fingerprint(actual) == _fingerprint(expected)


@pytest.mark.parametrize("call", PLOT_CALLS, ids=lambda call: call.key)
def test_plot_call_does_not_mutate_input(call: PlotCall, people):
    before = people.copy()
    resolved = call.resolve_params(call.example, people.columns.tolist())
    _draw_layer(call, people, resolved)
    pd.testing.assert_frame_equal(people, before)
