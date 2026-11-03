"""Plot calls that draw data: matplotlib ``Axes`` plotting methods.

Each entry adds one layer to the figure. Layers are drawn in order on
the same axes, so a scatter plot, a line and a histogram can be
combined freely.
"""

from __future__ import annotations

from typing import Any

from amazeplot.core.action import Params
from amazeplot.core.parameters import Parameter, ParameterKind
from amazeplot.core.plotting import AxesCall
from amazeplot.operations._common import (
    ALPHA,
    COLOR,
    COLORMAP,
    LEGEND_LABEL,
    LINESTYLE,
    LINEWIDTH,
    MARKER,
    ORIENTATION,
)

CATEGORY = "Plot"

_DEFAULT_BAR_WIDTH = 0.8
_DEFAULT_HEXBIN_GRIDSIZE = 100


def _column(
    name: str, label: str, *, required: bool = True, help: str = ""
) -> Parameter:
    """Return a parameter selecting one column."""
    return Parameter(
        name, label, ParameterKind.COLUMN, required=required, help=help
    )


def _columns(name: str, label: str) -> Parameter:
    """Return a required parameter selecting several columns."""
    return Parameter(name, label, ParameterKind.COLUMNS, required=True)


def _legend_labels(params: Params) -> dict[str, Any]:
    """Label every histogram dataset with its column name."""
    return {"label": [str(column) for column in params["x"]]}


def _tick_labels(params: Params) -> dict[str, Any]:
    """Label every box with its column name."""
    return {"tick_labels": [str(column) for column in params["x"]]}


LINE = AxesCall(
    key="plot_line",
    label="Line",
    category=CATEGORY,
    description=(
        "Draw y against x as lines and/or markers. Without x, the row "
        "position is used."
    ),
    parameters=(
        _column("x", "X", required=False, help="Leave empty to use 0..n."),
        _column("y", "Y"),
        COLOR,
        LINESTYLE,
        LINEWIDTH,
        MARKER,
        ALPHA,
        LEGEND_LABEL,
    ),
    method="plot",
    positional=("x", "y"),
)

SCATTER = AxesCall(
    key="plot_scatter",
    label="Scatter",
    category=CATEGORY,
    description="One marker per row at (x, y), optionally coloured.",
    parameters=(
        _column("x", "X"),
        _column("y", "Y"),
        Parameter(
            "s",
            "Marker size",
            ParameterKind.FLOAT,
            minimum=0.0,
            step=5.0,
            help="Area of each marker in points squared.",
        ),
        _column(
            "c",
            "Colour by column",
            required=False,
            help="Numeric column mapped through the colour map.",
        ),
        COLORMAP,
        COLOR,
        MARKER,
        ALPHA,
        LEGEND_LABEL,
    ),
    method="scatter",
    positional=("x", "y"),
)

BAR = AxesCall(
    key="plot_bar",
    label="Bar chart",
    category=CATEGORY,
    description="One vertical bar per row: categories on x, heights on y.",
    parameters=(
        _column("x", "Categories"),
        _column("height", "Heights"),
        Parameter(
            "width",
            "Bar width",
            ParameterKind.FLOAT,
            default=_DEFAULT_BAR_WIDTH,
            minimum=0.0,
            step=0.1,
        ),
        COLOR,
        ALPHA,
        LEGEND_LABEL,
    ),
    method="bar",
    positional=("x", "height"),
)

BARH = AxesCall(
    key="plot_barh",
    label="Horizontal bar chart",
    category=CATEGORY,
    description="One horizontal bar per row: categories on y.",
    parameters=(
        _column("y", "Categories"),
        _column("width", "Lengths"),
        Parameter(
            "height",
            "Bar thickness",
            ParameterKind.FLOAT,
            default=_DEFAULT_BAR_WIDTH,
            minimum=0.0,
            step=0.1,
        ),
        COLOR,
        ALPHA,
        LEGEND_LABEL,
    ),
    method="barh",
    positional=("y", "width"),
)

HISTOGRAM = AxesCall(
    key="plot_hist",
    label="Histogram",
    category=CATEGORY,
    description=(
        "Distribution of one or more numeric columns. Missing values are "
        "ignored; each column is labelled for the legend."
    ),
    parameters=(
        _columns("x", "Columns"),
        Parameter("bins", "Bins", ParameterKind.INTEGER, minimum=1),
        Parameter(
            "histtype",
            "Style",
            ParameterKind.CHOICE,
            default="bar",
            choices=("bar", "barstacked", "step", "stepfilled"),
        ),
        Parameter(
            "density",
            "Normalise (density)",
            ParameterKind.BOOLEAN,
            default=False,
        ),
        Parameter(
            "cumulative", "Cumulative", ParameterKind.BOOLEAN, default=False
        ),
        ORIENTATION,
        ALPHA,
    ),
    method="hist",
    positional=("x",),
    dropna=True,
    extra_kwargs=_legend_labels,
)

BOXPLOT = AxesCall(
    key="plot_box",
    label="Box plot",
    category=CATEGORY,
    description=(
        "Median, quartiles and outliers of one or more numeric columns. "
        "Missing values are ignored."
    ),
    parameters=(
        _columns("x", "Columns"),
        Parameter("notch", "Notched", ParameterKind.BOOLEAN, default=False),
        Parameter(
            "showmeans", "Show means", ParameterKind.BOOLEAN, default=False
        ),
        ORIENTATION,
    ),
    method="boxplot",
    positional=("x",),
    dropna=True,
    extra_kwargs=_tick_labels,
)

PIE = AxesCall(
    key="plot_pie",
    label="Pie chart",
    category=CATEGORY,
    description="Slices proportional to the values of one column.",
    parameters=(
        _column("x", "Values"),
        _column("labels", "Slice labels", required=False),
        Parameter(
            "autopct",
            "Value format",
            ParameterKind.TEXT,
            help="E.g. %1.1f%% to print percentages on the slices.",
        ),
        Parameter(
            "startangle",
            "Start angle",
            ParameterKind.FLOAT,
            default=0.0,
            minimum=-360.0,
            maximum=360.0,
            step=15.0,
        ),
    ),
    method="pie",
    positional=("x",),
)

AREA = AxesCall(
    key="plot_area",
    label="Area",
    category=CATEGORY,
    description="Fill the area between two curves (or a curve and 0).",
    parameters=(
        _column("x", "X"),
        _column("y1", "Upper curve"),
        _column("y2", "Lower curve", required=False, help="Default: 0."),
        COLOR,
        ALPHA,
        LEGEND_LABEL,
    ),
    method="fill_between",
    positional=("x", "y1", "y2"),
)

STEP = AxesCall(
    key="plot_step",
    label="Step",
    category=CATEGORY,
    description="A staircase line, for piecewise-constant data.",
    parameters=(
        _column("x", "X"),
        _column("y", "Y"),
        Parameter(
            "where",
            "Step position",
            ParameterKind.CHOICE,
            default="pre",
            choices=("pre", "post", "mid"),
        ),
        COLOR,
        LINESTYLE,
        LINEWIDTH,
        LEGEND_LABEL,
    ),
    method="step",
    positional=("x", "y"),
)

STEM = AxesCall(
    key="plot_stem",
    label="Stem",
    category=CATEGORY,
    description="A vertical line from the baseline to each value.",
    parameters=(
        _column("locs", "X", required=False, help="Leave empty for 0..n."),
        _column("heads", "Y"),
        LEGEND_LABEL,
    ),
    method="stem",
    positional=("locs", "heads"),
)

ERRORBAR = AxesCall(
    key="plot_errorbar",
    label="Error bars",
    category=CATEGORY,
    description="Points or lines with error bars taken from columns.",
    parameters=(
        _column("x", "X"),
        _column("y", "Y"),
        _column("yerr", "Y error", required=False),
        _column("xerr", "X error", required=False),
        Parameter(
            "fmt",
            "Format",
            ParameterKind.TEXT,
            help="E.g. o for points only, -o for line and points.",
        ),
        Parameter("capsize", "Cap size", ParameterKind.FLOAT, minimum=0.0),
        COLOR,
        LEGEND_LABEL,
    ),
    method="errorbar",
    positional=("x", "y"),
)

HEXBIN = AxesCall(
    key="plot_hexbin",
    label="Hexagonal density",
    category=CATEGORY,
    description="Count of points in hexagonal cells, for large scatters.",
    parameters=(
        _column("x", "X"),
        _column("y", "Y"),
        Parameter(
            "gridsize",
            "Cells across",
            ParameterKind.INTEGER,
            default=_DEFAULT_HEXBIN_GRIDSIZE,
            minimum=1,
        ),
        Parameter(
            "mincnt",
            "Hide cells below",
            ParameterKind.INTEGER,
            minimum=0,
            help="Only show cells with at least this many points.",
        ),
        COLORMAP,
    ),
    method="hexbin",
    positional=("x", "y"),
)

HEATMAP = AxesCall(
    key="plot_heatmap",
    label="Heatmap",
    category=CATEGORY,
    description=(
        "Draw the numeric columns of the whole table as an image, one "
        "cell per value. Tip: apply Correlation matrix first."
    ),
    parameters=(
        COLORMAP,
        Parameter(
            "aspect",
            "Cell shape",
            ParameterKind.CHOICE,
            choices=(None, "equal", "auto"),
        ),
        Parameter("vmin", "Colour minimum", ParameterKind.FLOAT),
        Parameter("vmax", "Colour maximum", ParameterKind.FLOAT),
    ),
    method="imshow",
    numeric_frame=True,
)

ACTIONS = (
    LINE,
    SCATTER,
    BAR,
    BARH,
    HISTOGRAM,
    BOXPLOT,
    PIE,
    AREA,
    STEP,
    STEM,
    ERRORBAR,
    HEXBIN,
    HEATMAP,
)
