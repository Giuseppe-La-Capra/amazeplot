import numpy as np
import pytest

from amazeplot.core.formatting import (
    MISSING_TEXT,
    describe_label,
    format_label,
    format_value,
)


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (np.float64(7570.0), "7570.0"),
        (np.int64(3), "3"),
        (complex(-2385311.5, 12.25), "-2385311.5+12.25j"),
        (np.complex128(3 - 4j), "3-4j"),
        (None, MISSING_TEXT),
        (float("nan"), MISSING_TEXT),
        (complex("nan+0j"), MISSING_TEXT),
        ("text", "text"),
    ],
)
def test_format_value(value, text):
    assert format_value(value) == text


def test_format_label_joins_levels():
    label = (np.float64(7570.0), np.int64(0), 0)
    assert format_label(label) == "7570.0 | 0 | 0"
    assert format_label("plain") == "plain"


def test_describe_label_names_levels():
    label = (7570.0, 0, 0)
    assert describe_label(label, ["freq", None, "j"]) == "freq=7570.0, 0, j=0"
    assert describe_label("x", [None]) == "x"
    # A tuple used as a single label (names do not match): plain text.
    assert describe_label(("a", "b"), [None]) == "a | b"
