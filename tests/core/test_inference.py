import numpy as np
import pandas as pd

from amazeplot.core.inference import complex_text_columns


def test_detects_complex_text():
    frame = pd.DataFrame(
        {
            "z": ["(1+2j)", None, "(-3.5-0.5j)", "4"],
            "words": ["a", "b", "c", "d"],
            "numbers_as_text": ["1", "2", "3", "4"],
            "z_native": np.array([1j, 2, 3, 4], dtype=complex),
            "n": [1, 2, 3, 4],
        }
    )
    assert complex_text_columns(frame) == ["z"]


def test_ignores_columns_with_other_text():
    frame = pd.DataFrame({"z": ["(1+2j)", "not a number"]})
    assert complex_text_columns(frame) == []


def test_empty_and_all_missing_columns():
    frame = pd.DataFrame({"z": pd.Series([None, None], dtype=object)})
    assert complex_text_columns(frame) == []
    assert complex_text_columns(pd.DataFrame()) == []


def test_only_a_sample_is_inspected():
    values = ["1+1j"] * 5 + ["oops"]
    frame = pd.DataFrame({"z": values})
    assert complex_text_columns(frame, sample_size=5) == ["z"]
    assert complex_text_columns(frame, sample_size=6) == []
