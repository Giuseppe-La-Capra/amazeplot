"""Shared fixtures for the whole test-suite."""

import os

import pandas as pd
import pytest

# Run Qt and matplotlib without a display (CI, containers). These must
# be set before Qt or matplotlib load.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")


@pytest.fixture
def people() -> pd.DataFrame:
    """A small frame with numbers, text, missing values and duplicates."""
    return pd.DataFrame(
        {
            "name": ["Ann", "Bob", "Cid", "Dan", "Bob"],
            "city": ["Rome", "Oslo", "Rome", None, "Oslo"],
            "age": [31, 25, None, 47, 25],
            "score": [7.5, 8.0, 6.5, 9.0, 8.0],
        }
    )
