"""Facts about one column or one row, for the Data tab's info panel.

The summaries are computed with pandas over the *whole* DataFrame (not
just the rows on screen) and returned as display text, grouped in
sections. Columns and rows are addressed by position, so duplicate
labels are handled.
"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd
from pandas.api import types as ptypes

from amazeplot.core.formatting import (
    describe_label,
    format_label,
    format_value,
)

Fields = list[tuple[str, str]]
"""(name, value) pairs shown as two columns."""

Sections = dict[str, Fields]
"""Ordered sections of fields, e.g. ``{"Column": [...], ...}``."""

ROW_VALUES_LIMIT = 50
"""Cells listed for a row; wider tables end with a "more columns" line."""

_BYTE_UNITS = ("bytes", "KB", "MB", "GB", "TB")
_BYTE_STEP = 1024


def column_summary(frame: pd.DataFrame, position: int) -> Sections:
    """Describe the column at ``position`` (0-based).

    Returns a "Column" section (name, position, dtype, counts, memory)
    and a "Statistics" section that depends on the type: minimum,
    maximum, mean and spread for numbers; mean and magnitudes for complex
    numbers; earliest and latest for dates; the most common value
    otherwise.

    Raises
    ------
    IndexError
        If there is no column at ``position``.
    """
    series = frame.iloc[:, position]
    missing = int(series.isna().sum())
    column: Fields = [
        ("Name", format_label(frame.columns[position])),
        ("Position", f"{position + 1:,} of {len(frame.columns):,}"),
        ("Type (dtype)", str(series.dtype)),
        ("Values", f"{len(series) - missing:,}"),
        ("Missing", f"{missing:,}"),
        ("Unique values", _unique_count(series)),
        ("Memory", _bytes_text(series.memory_usage(index=False))),
    ]
    return {"Column": column, "Statistics": _statistics(series)}


def row_summary(
    frame: pd.DataFrame, position: int, limit: int = ROW_VALUES_LIMIT
) -> Sections:
    """Describe the row at ``position`` (0-based).

    Returns a "Row" section (position, label with level names, missing
    count) and a "Values" section listing the first ``limit`` cells in
    full, which helps when a narrow column cuts a value off.

    Raises
    ------
    IndexError
        If there is no row at ``position``.
    """
    values = frame.iloc[position]
    index = frame.index
    row: Fields = [
        ("Position", f"{position + 1:,} of {len(index):,}"),
        ("Label", format_label(index[position])),
    ]
    if any(name is not None for name in index.names):
        row.append(("Levels", describe_label(index[position], index.names)))
    row.append(("Missing", f"{int(values.isna().sum()):,}"))
    cells: Fields = [
        (format_label(label), format_value(value))
        for label, value in zip(
            frame.columns[:limit], values.iloc[:limit], strict=True
        )
    ]
    if len(frame.columns) > limit:
        cells.append(("...", f"{len(frame.columns) - limit:,} more columns"))
    return {"Row": row, "Values": cells}


# -- Statistics by type --------------------------------------------------


def _number_statistics(series: pd.Series) -> Fields:
    return [
        ("Minimum", format_value(series.min())),
        ("Maximum", format_value(series.max())),
        ("Mean", format_value(series.mean())),
        ("Standard deviation", format_value(series.std())),
    ]


def _complex_statistics(series: pd.Series) -> Fields:
    # Complex numbers have no order: report their magnitudes instead.
    magnitude = series.abs()
    return [
        ("Mean", format_value(series.mean())),
        ("Smallest magnitude", format_value(magnitude.min())),
        ("Largest magnitude", format_value(magnitude.max())),
    ]


def _bool_statistics(series: pd.Series) -> Fields:
    return [("True", f"{int(series.sum()):,}")]


def _datetime_statistics(series: pd.Series) -> Fields:
    return [
        ("Earliest", format_value(series.min())),
        ("Latest", format_value(series.max())),
    ]


def _other_statistics(series: pd.Series) -> Fields:
    try:
        counts = series.value_counts()
    except TypeError:  # Unhashable cells, e.g. lists.
        return []
    if counts.empty:
        return []
    value, count = counts.index[0], counts.iloc[0]
    return [("Most common", f"{format_value(value)} ({count:,} times)")]


_STATISTICS: tuple[
    tuple[Callable[[pd.Series], bool], Callable[[pd.Series], Fields]], ...
] = (
    (ptypes.is_bool_dtype, _bool_statistics),
    (ptypes.is_complex_dtype, _complex_statistics),
    (ptypes.is_numeric_dtype, _number_statistics),
    (ptypes.is_datetime64_any_dtype, _datetime_statistics),
)
"""(dtype test, statistics) pairs, checked in order; first match wins."""


def _statistics(series: pd.Series) -> Fields:
    for matches, statistics in _STATISTICS:
        if matches(series):
            return statistics(series)
    return _other_statistics(series)


# -- Formatting helpers --------------------------------------------------


def _unique_count(series: pd.Series) -> str:
    try:
        return f"{series.nunique():,}"
    except TypeError:  # Unhashable cells, e.g. lists.
        return "n/a"


def _bytes_text(size: float) -> str:
    unit = 0
    while size >= _BYTE_STEP and unit < len(_BYTE_UNITS) - 1:
        size /= _BYTE_STEP
        unit += 1
    decimals = 0 if unit == 0 else 1
    return f"{size:,.{decimals}f} {_BYTE_UNITS[unit]}"
