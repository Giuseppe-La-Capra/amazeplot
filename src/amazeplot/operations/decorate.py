"""Plot calls that decorate the axes: titles, labels, scales, guides.

These take no data columns. They are layers too, so they can be undone
and they appear in the exported script in the order they were added.
"""

from __future__ import annotations

from amazeplot.core.parameters import Parameter, ParameterKind
from amazeplot.core.plotting import AxesCall
from amazeplot.operations._common import (
    ALPHA,
    COLOR,
    LEGEND_LABEL,
    LINESTYLE,
    LINEWIDTH,
)

CATEGORY = "Decorate"

_SCALES = ("linear", "log", "symlog", "logit")
_AXIS_CHOICES = ("both", "x", "y")
_LEGEND_LOCATIONS = (
    None,
    "best",
    "upper right",
    "upper left",
    "lower left",
    "lower right",
    "right",
    "center left",
    "center right",
    "lower center",
    "upper center",
    "center",
)


def _text(name: str, label: str) -> Parameter:
    """Return a required text parameter."""
    return Parameter(name, label, ParameterKind.TEXT, required=True)


def _optional_float(name: str, label: str) -> Parameter:
    """Return an optional float parameter (``None`` = automatic)."""
    return Parameter(name, label, ParameterKind.FLOAT)


TITLE = AxesCall(
    key="set_title",
    label="Title",
    category=CATEGORY,
    description="Set the title above the plot.",
    parameters=(
        _text("label", "Title"),
        Parameter(
            "loc",
            "Alignment",
            ParameterKind.CHOICE,
            choices=(None, "center", "left", "right"),
        ),
    ),
    method="set_title",
    positional=("label",),
)

XLABEL = AxesCall(
    key="set_xlabel",
    label="X axis label",
    category=CATEGORY,
    description="Set the label of the horizontal axis.",
    parameters=(_text("xlabel", "Label"),),
    method="set_xlabel",
    positional=("xlabel",),
)

YLABEL = AxesCall(
    key="set_ylabel",
    label="Y axis label",
    category=CATEGORY,
    description="Set the label of the vertical axis.",
    parameters=(_text("ylabel", "Label"),),
    method="set_ylabel",
    positional=("ylabel",),
)

LEGEND = AxesCall(
    key="legend",
    label="Legend",
    category=CATEGORY,
    description=(
        "Show a legend for the layers that have a legend label. Add it "
        "after the layers it describes."
    ),
    parameters=(
        Parameter(
            "loc",
            "Position",
            ParameterKind.CHOICE,
            choices=_LEGEND_LOCATIONS,
        ),
        Parameter("title", "Title", ParameterKind.TEXT),
        Parameter("ncols", "Columns", ParameterKind.INTEGER, minimum=1),
    ),
    method="legend",
)

GRID = AxesCall(
    key="grid",
    label="Grid",
    category=CATEGORY,
    description="Show or hide grid lines.",
    parameters=(
        Parameter("visible", "Show grid", ParameterKind.BOOLEAN, default=True),
        Parameter(
            "axis",
            "Axes",
            ParameterKind.CHOICE,
            default="both",
            choices=_AXIS_CHOICES,
        ),
        LINESTYLE,
        ALPHA,
    ),
    method="grid",
    positional=("visible",),
)

XSCALE = AxesCall(
    key="set_xscale",
    label="X axis scale",
    category=CATEGORY,
    description="Use a linear, logarithmic, ... horizontal axis.",
    parameters=(
        Parameter(
            "value",
            "Scale",
            ParameterKind.CHOICE,
            default="log",
            required=True,
            choices=_SCALES,
        ),
    ),
    method="set_xscale",
    positional=("value",),
)

YSCALE = AxesCall(
    key="set_yscale",
    label="Y axis scale",
    category=CATEGORY,
    description="Use a linear, logarithmic, ... vertical axis.",
    parameters=(
        Parameter(
            "value",
            "Scale",
            ParameterKind.CHOICE,
            default="log",
            required=True,
            choices=_SCALES,
        ),
    ),
    method="set_yscale",
    positional=("value",),
)

XLIM = AxesCall(
    key="set_xlim",
    label="X axis range",
    category=CATEGORY,
    description="Fix the visible range of the horizontal axis.",
    parameters=(
        _optional_float("left", "From"),
        _optional_float("right", "To"),
    ),
    method="set_xlim",
)

YLIM = AxesCall(
    key="set_ylim",
    label="Y axis range",
    category=CATEGORY,
    description="Fix the visible range of the vertical axis.",
    parameters=(
        _optional_float("bottom", "From"),
        _optional_float("top", "To"),
    ),
    method="set_ylim",
)

HLINE = AxesCall(
    key="axhline",
    label="Horizontal line",
    category=CATEGORY,
    description="A horizontal reference line across the whole plot.",
    parameters=(
        Parameter("y", "At y", ParameterKind.FLOAT, default=0.0),
        COLOR,
        LINESTYLE,
        LINEWIDTH,
        LEGEND_LABEL,
    ),
    method="axhline",
)

VLINE = AxesCall(
    key="axvline",
    label="Vertical line",
    category=CATEGORY,
    description="A vertical reference line across the whole plot.",
    parameters=(
        Parameter("x", "At x", ParameterKind.FLOAT, default=0.0),
        COLOR,
        LINESTYLE,
        LINEWIDTH,
        LEGEND_LABEL,
    ),
    method="axvline",
)

TEXT = AxesCall(
    key="text",
    label="Text",
    category=CATEGORY,
    description="Write text at a position given in data coordinates.",
    parameters=(
        Parameter("x", "X", ParameterKind.FLOAT, required=True),
        Parameter("y", "Y", ParameterKind.FLOAT, required=True),
        _text("s", "Text"),
        _optional_float("fontsize", "Font size"),
        COLOR,
    ),
    method="text",
    positional=("x", "y", "s"),
)

TICKS = AxesCall(
    key="tick_params",
    label="Tick labels",
    category=CATEGORY,
    description="Rotate or resize the tick labels, e.g. long bar names.",
    parameters=(
        Parameter(
            "axis",
            "Axes",
            ParameterKind.CHOICE,
            default="both",
            choices=_AXIS_CHOICES,
        ),
        Parameter(
            "labelrotation",
            "Rotation (degrees)",
            ParameterKind.FLOAT,
            minimum=-360.0,
            maximum=360.0,
            step=15.0,
        ),
        _optional_float("labelsize", "Font size"),
    ),
    method="tick_params",
)

ACTIONS = (
    TITLE,
    XLABEL,
    YLABEL,
    LEGEND,
    GRID,
    XSCALE,
    YSCALE,
    XLIM,
    YLIM,
    HLINE,
    VLINE,
    TEXT,
    TICKS,
)
