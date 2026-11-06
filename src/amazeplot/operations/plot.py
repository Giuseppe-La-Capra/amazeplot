"""Plot calls that draw data: matplotlib ``Axes`` plotting methods.

Each entry adds one layer to the figure. Layers are drawn in order on
the same axes, so a scatter plot, a line and a histogram can be
combined freely.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
from matplotlib.axes import Axes

from amazeplot.core.action import Params, format_call_arguments
from amazeplot.core.parameters import Parameter, ParameterKind, is_empty
from amazeplot.core.plotting import (
    AXES_VARIABLE,
    FIGURE_VARIABLE,
    MATPLOTLIB_API_URL,
    AxesCall,
    PlotCall,
)
from amazeplot.operations._common import (
    AGGREGATIONS,
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
    example={"x": "age", "y": "score", "marker": "o", "label": "s"},
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
    example={"x": "age", "y": "score", "c": "score", "s": 40.0},
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
    example={"x": "name", "height": "score", "color": "tab:red"},
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
    example={"y": "name", "width": "score", "height": 0.5},
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
    example={"x": ["age", "score"], "bins": 5},
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
    example={"x": ["age", "score"], "showmeans": True},
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
    example={"x": "score", "labels": "name", "autopct": "%1.0f%%"},
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
    example={"x": "score", "y1": "age", "alpha": 0.3},
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
    example={"x": "score", "y": "age", "where": "mid"},
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
    example={"heads": "score"},
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
    example={"x": "score", "y": "age", "yerr": "score"},
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
    example={"x": "age", "y": "score", "gridsize": 5},
    label="Hexagonal density",
    category=CATEGORY,
    description=(
        "Hexagonal cells over X and Y, coloured by how many points fall "
        "in each, or by the mean of a Values column. Good for large "
        "scatters. Add Decorate > Colour bar to show the scale."
    ),
    parameters=(
        _column("x", "X"),
        _column("y", "Y"),
        _column(
            "C",
            "Values",
            required=False,
            help="Colour by the mean of this column instead of counts.",
        ),
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


@dataclass(frozen=True)
class HeatmapCall(PlotCall):
    """Values laid out on an X by Y grid, one coloured cell per pair.

    The rows are first arranged with ``pivot_table`` (several rows with
    the same X and Y are combined with the chosen function), then drawn
    with ``pcolormesh``, which accepts numeric and text categories.
    A custom class because the code is several statements.
    """

    @property
    def documentation_url(self) -> str:
        """Return the matplotlib documentation page of ``pcolormesh``."""
        return MATPLOTLIB_API_URL.format("pcolormesh")

    def _draw(self, frame: pd.DataFrame, params: Params, axes: Axes) -> None:
        grid = frame.pivot_table(
            index=params["y"],
            columns=params["x"],
            values=params["values"],
            aggfunc=params["aggfunc"],
        )
        mesh = axes.pcolormesh(
            grid.columns, grid.index, grid, **_mesh_kwargs(params)
        )
        if params["colorbar"]:
            axes.figure.colorbar(mesh, ax=axes, label=str(params["values"]))

    def to_code(self, params: Params, variable: str = "df") -> str:
        """Return the pivot, ``pcolormesh`` and colour-bar statements."""
        pivot = format_call_arguments(
            index=params["y"],
            columns=params["x"],
            values=params["values"],
            aggfunc=params["aggfunc"],
        )
        mesh = format_call_arguments(**_mesh_kwargs(params))
        lines = [
            f"grid = {variable}.pivot_table({pivot})",
            f"mesh = {AXES_VARIABLE}.pcolormesh("
            f"grid.columns, grid.index, grid, {mesh})",
        ]
        if params["colorbar"]:
            label = format_call_arguments(label=str(params["values"]))
            lines.append(
                f"{FIGURE_VARIABLE}.colorbar(mesh, ax={AXES_VARIABLE}, "
                f"{label})"
            )
        return "\n".join(lines)


def _mesh_kwargs(params: Params) -> dict[str, Any]:
    """Keyword arguments of ``pcolormesh``: automatic options left out."""
    kwargs: dict[str, Any] = {"shading": "auto"}
    for name in ("cmap", "vmin", "vmax"):
        if not is_empty(params[name]):
            kwargs[name] = params[name]
    return kwargs


HEATMAP = HeatmapCall(
    key="plot_heatmap",
    example={"x": "city", "y": "name", "values": "score"},
    label="Heatmap",
    category=CATEGORY,
    description=(
        "A grid with X across and Y down, each cell coloured by the "
        "Values column. Rows sharing the same X and Y are combined with "
        "the chosen function; cells without data stay empty. Tip: for "
        "complex numbers, first create their magnitude or phase."
    ),
    parameters=(
        _column("x", "X (across)"),
        _column("y", "Y (down)"),
        _column("values", "Values"),
        Parameter(
            "aggfunc",
            "Combine repeated cells with",
            ParameterKind.CHOICE,
            default="mean",
            required=True,
            choices=AGGREGATIONS,
        ),
        COLORMAP,
        Parameter("vmin", "Colour minimum", ParameterKind.FLOAT),
        Parameter("vmax", "Colour maximum", ParameterKind.FLOAT),
        Parameter(
            "colorbar",
            "Show colour bar",
            ParameterKind.BOOLEAN,
            default=True,
        ),
    ),
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
