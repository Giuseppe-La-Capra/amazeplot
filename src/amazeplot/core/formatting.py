"""Turn cell values and row/column labels into display text.

Every view (table, editors, info panel) formats through this module, so
a value looks the same everywhere. Display only: the data itself is
never changed.
"""

from __future__ import annotations

from collections.abc import Hashable
from typing import Any

import numpy as np
import pandas as pd
from pandas.api import types as ptypes

MISSING_TEXT = "NaN"
"""Text displayed for missing values."""

LEVEL_SEPARATOR = " | "
"""Separator between the levels of a multi-level (MultiIndex) label."""


def is_missing(value: Any) -> bool:
    """Return whether ``value`` is a scalar missing value."""
    return ptypes.is_scalar(value) and bool(pd.isna(value))


def format_value(value: Any) -> str:
    """Return the text shown for one cell value.

    numpy scalars are shown like the equivalent Python value (``7570.0``
    rather than ``np.float64(7570.0)``), and complex numbers without
    Python's parentheses (``1.5-2j`` rather than ``(1.5-2j)``). Full
    precision is kept.
    """
    if is_missing(value):
        return MISSING_TEXT
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, complex):
        return str(value).strip("()")
    return str(value)


def format_label(label: Hashable) -> str:
    """Return the text shown for a row or column label.

    The levels of a multi-level label (a tuple) are joined with
    :data:`LEVEL_SEPARATOR`, e.g. ``7570.0 | 0 | 0``.
    """
    if isinstance(label, tuple):
        return LEVEL_SEPARATOR.join(format_label(part) for part in label)
    return format_value(label)


def describe_label(label: Hashable, names: list[Hashable | None]) -> str:
    """Return a label with its level names, e.g. ``freq=7570.0, i=0``.

    Parameters
    ----------
    label : Hashable
        A row or column label; a tuple for a multi-level index.
    names : list
        The index level names (``index.names``); unnamed levels are
        ``None`` and are shown without a name.
    """
    parts = label if isinstance(label, tuple) else (label,)
    if len(parts) != len(names):
        # A tuple used as a plain label: there are no level names.
        return format_label(label)
    return ", ".join(
        format_label(part) if name is None else f"{name}={format_label(part)}"
        for name, part in zip(names, parts, strict=True)
    )
