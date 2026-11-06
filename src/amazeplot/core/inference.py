"""Recognise column types that file formats lose.

CSV and other text formats store complex numbers as text such as
``(1.5-2j)``, so pandas reads them back as strings. The functions here
spot such columns; the GUI then converts them with an ordinary,
undoable "Change column type" step that also appears in the exported
script.
"""

from __future__ import annotations

from collections.abc import Hashable

import pandas as pd
from pandas.api import types as ptypes

COMPLEX_DTYPE = "complex128"
"""dtype used for columns of complex numbers."""

SAMPLE_SIZE = 100
"""Non-missing values inspected per column; the rest is converted."""

_IMAGINARY_UNIT = "j"


def complex_text_columns(
    frame: pd.DataFrame, sample_size: int = SAMPLE_SIZE
) -> list[Hashable]:
    """Return the labels of text columns that hold complex numbers.

    A column qualifies when its first ``sample_size`` non-missing values
    are all text that Python's :class:`complex` can parse, and at least
    one of them has an imaginary part (so plain numbers stored as text
    are left alone). Only a sample is checked to stay fast on large
    tables; converting the whole column may still fail, and the caller
    then keeps it as text.
    """
    labels = []
    for label, series in frame.items():
        if not _is_text(series):
            continue
        sample = series.dropna().head(sample_size).tolist()
        if (
            sample
            and all(_is_complex_text(value) for value in sample)
            and any(_IMAGINARY_UNIT in value for value in sample)
        ):
            labels.append(label)
    return labels


def _is_text(series: pd.Series) -> bool:
    return ptypes.is_object_dtype(series) or ptypes.is_string_dtype(series)


def _is_complex_text(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        complex(value.replace(" ", ""))
    except ValueError:
        return False
    return True
