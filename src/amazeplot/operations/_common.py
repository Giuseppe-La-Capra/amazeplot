"""Parameter definitions shared by several operation modules."""

from amazeplot.core.parameters import Parameter, ParameterKind

ROW_COUNT = Parameter(
    name="n",
    label="Rows",
    kind=ParameterKind.INTEGER,
    default=5,
    minimum=0,
    help="Number of rows to keep.",
)

SUBSET = Parameter(
    name="subset",
    label="Columns",
    kind=ParameterKind.COLUMNS,
    help="Only consider these columns (default: all columns).",
)

AGGREGATIONS = (
    "sum",
    "mean",
    "median",
    "min",
    "max",
    "count",
    "nunique",
    "std",
    "var",
    "first",
    "last",
)
"""Aggregation function names accepted by pandas ``agg``."""

# -- Plot styling -------------------------------------------------------
# Defaults are None ("let matplotlib decide"), so untouched options are
# left out of the call and of the generated code.

COLOR = Parameter(
    name="color",
    label="Colour",
    kind=ParameterKind.TEXT,
    help="A colour name or hex code, e.g. tab:red or #1f77b4.",
)

ALPHA = Parameter(
    name="alpha",
    label="Opacity",
    kind=ParameterKind.FLOAT,
    minimum=0.0,
    maximum=1.0,
    step=0.1,
    help="From 0 (transparent) to 1 (opaque).",
)

LEGEND_LABEL = Parameter(
    name="label",
    label="Legend label",
    kind=ParameterKind.TEXT,
    help="Text shown for this layer by the Legend decoration.",
)

LINESTYLE = Parameter(
    name="linestyle",
    label="Line style",
    kind=ParameterKind.CHOICE,
    choices=(None, "-", "--", ":", "-."),
)

LINEWIDTH = Parameter(
    name="linewidth",
    label="Line width",
    kind=ParameterKind.FLOAT,
    minimum=0.0,
    step=0.5,
)

MARKER = Parameter(
    name="marker",
    label="Marker",
    kind=ParameterKind.CHOICE,
    choices=(None, "o", ".", "s", "^", "v", "D", "x", "+", "*"),
)

COLORMAP = Parameter(
    name="cmap",
    label="Colour map",
    kind=ParameterKind.CHOICE,
    choices=(
        None,
        "viridis",
        "plasma",
        "inferno",
        "magma",
        "cividis",
        "coolwarm",
        "RdBu",
        "Greys",
        "Blues",
    ),
)

ORIENTATION = Parameter(
    name="orientation",
    label="Orientation",
    kind=ParameterKind.CHOICE,
    default="vertical",
    choices=("vertical", "horizontal"),
)
