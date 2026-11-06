"""Built-in example data, used by the help pages and *Open example data*.

The table has the columns every catalogue ``example`` refers to:
``name``, ``city``, ``age`` and ``score``. It deliberately contains a
missing age, a missing city and a duplicated row, so the cleaning
operations have something to do.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from amazeplot.core.errors import DataIOError
from amazeplot.core.io import save_dataframe

EXAMPLE_FILE_NAME = "amazeplot-example.csv"
"""File name used when the example data is written to disk."""

EXAMPLE_COLUMNS: tuple[str, ...] = ("name", "city", "age", "score")
"""Columns of :func:`example_data`, in order."""


def example_data() -> pd.DataFrame:
    """Return a new copy of the example table (12 people)."""
    return pd.DataFrame(
        {
            "name": [
                "Ann", "Bob", "Cid", "Dan", "Eve", "Fay",
                "Gus", "Hal", "Ivy", "Jon", "Kim", "Bob",
            ],
            "city": [
                "Rome", "Oslo", "Rome", None, "Lima", "Oslo",
                "Lima", "Rome", "Oslo", "Lima", "Rome", "Oslo",
            ],
            "age": [31, 25, None, 47, 38, 29, 52, 44, 23, 35, 41, 25],
            "score": [
                7.5, 8.0, 6.5, 9.0, 7.0, 8.5,
                6.0, 7.5, 9.5, 6.5, 8.0, 8.0,
            ],
        },
        columns=list(EXAMPLE_COLUMNS),
    )  # fmt: skip


def write_example_data(directory: Path | str) -> Path:
    """Write the example table as CSV into ``directory`` and return it.

    The directory is created if needed. An existing file is replaced, so
    the example always starts from the same data.

    Raises
    ------
    DataIOError
        If the file cannot be written.
    """
    directory = Path(directory)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DataIOError(f"Cannot create {directory}: {exc}") from exc
    path = directory / EXAMPLE_FILE_NAME
    save_dataframe(example_data(), path)
    return path
