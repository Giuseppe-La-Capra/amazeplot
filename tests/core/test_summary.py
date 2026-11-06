import numpy as np
import pandas as pd
import pytest

from amazeplot.core.summary import column_summary, row_summary


def _fields(sections, name):
    return dict(sections[name])


def test_numeric_column(people):
    summary = column_summary(people, 2)  # age
    column = _fields(summary, "Column")
    assert column["Name"] == "age"
    assert column["Position"] == "3 of 4"
    assert column["Type (dtype)"] == "float64"
    assert (column["Values"], column["Missing"]) == ("4", "1")
    assert column["Unique values"] == "3"
    stats = _fields(summary, "Statistics")
    assert (stats["Minimum"], stats["Maximum"]) == ("25.0", "47.0")
    assert stats["Mean"] == "32.0"


def test_complex_column():
    frame = pd.DataFrame({"z": np.array([3 + 4j, -1j, np.nan])})
    stats = _fields(column_summary(frame, 0), "Statistics")
    assert stats["Smallest magnitude"] == "1.0"
    assert stats["Largest magnitude"] == "5.0"
    assert "Minimum" not in stats  # Complex numbers have no order.


def test_text_bool_and_date_columns(people):
    stats = _fields(column_summary(people, 1), "Statistics")  # city
    assert stats["Most common"] in ("Rome (2 times)", "Oslo (2 times)")
    flags = pd.DataFrame({"ok": [True, False, True]})
    assert _fields(column_summary(flags, 0), "Statistics") == {"True": "2"}
    dates = pd.DataFrame({"d": pd.to_datetime(["2024-01-02", "2023-05-06"])})
    stats = _fields(column_summary(dates, 0), "Statistics")
    assert stats["Earliest"].startswith("2023-05-06")


def test_unhashable_cells():
    frame = pd.DataFrame({"lists": [[1], [2]]})
    # Must not crash. Whether pandas can count list values depends on
    # its version, so only check what is shown when it can't.
    summary = column_summary(frame, 0)
    assert _fields(summary, "Column")["Unique values"] == "n/a"
    assert set(_fields(summary, "Statistics")) <= {"Most common"}


def test_duplicate_column_labels_use_positions():
    frame = pd.DataFrame([[1, "a"]], columns=["x", "x"])
    assert _fields(column_summary(frame, 1), "Column")["Type (dtype)"] in (
        "object",
        "str",
    )


def test_row_with_multi_level_label():
    index = pd.MultiIndex.from_tuples(
        [(7570.0, 0, 0), (7570.0, 1, 0)], names=["freq", "i", "j"]
    )
    frame = pd.DataFrame({"value": [1 + 2j, np.nan]}, index=index)
    summary = row_summary(frame, 1)
    row = _fields(summary, "Row")
    assert row["Position"] == "2 of 2"
    assert row["Label"] == "7570.0 | 1 | 0"
    assert row["Levels"] == "freq=7570.0, i=1, j=0"
    assert row["Missing"] == "1"
    assert _fields(summary, "Values") == {"value": "NaN"}


def test_row_values_are_limited():
    frame = pd.DataFrame([range(60)])
    values = row_summary(frame, 0, limit=50)["Values"]
    assert len(values) == 51
    assert values[-1] == ("...", "10 more columns")


def test_out_of_range():
    with pytest.raises(IndexError):
        column_summary(pd.DataFrame({"a": [1]}), 5)
