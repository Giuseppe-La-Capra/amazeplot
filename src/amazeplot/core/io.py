"""Reading and writing DataFrames from and to files.

Supported formats are chosen by file extension. Each reader is described
by a :class:`DataSource`, which can both load the data and emit the
equivalent ``pandas`` call for the exported script.

Pickle files (``.pkl``, ``.pickle``) can be read, but unpickling can
run arbitrary code hidden in the file. They are listed in
:data:`UNSAFE_EXTENSIONS`, and callers must get the user's explicit
consent (see :func:`executes_code_on_read`) before loading one. Pickles
are never written.
"""

from __future__ import annotations

import pickle
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pandas as pd

from amazeplot.core.action import format_call_arguments
from amazeplot.core.errors import DataIOError

_READERS: Mapping[str, tuple[str, Mapping[str, Any]]] = MappingProxyType(
    {
        ".csv": ("read_csv", {}),
        ".tsv": ("read_csv", {"sep": "\t"}),
        ".json": ("read_json", {}),
        ".xlsx": ("read_excel", {}),
        ".parquet": ("read_parquet", {}),
        ".pkl": ("read_pickle", {}),
        ".pickle": ("read_pickle", {}),
    }
)

_WRITERS: Mapping[str, tuple[str, Mapping[str, Any]]] = MappingProxyType(
    {
        ".csv": ("to_csv", {"index": False}),
        ".tsv": ("to_csv", {"index": False, "sep": "\t"}),
        ".json": ("to_json", {"orient": "records", "indent": 2}),
        ".xlsx": ("to_excel", {"index": False}),
        ".parquet": ("to_parquet", {"index": False}),
    }
)

READABLE_EXTENSIONS: tuple[str, ...] = tuple(_READERS)
"""File extensions that :func:`load_dataframe` understands."""

UNSAFE_EXTENSIONS: frozenset[str] = frozenset({".pkl", ".pickle"})
"""Readable extensions whose loading can execute code from the file."""

_READ_ERRORS = (
    OSError,
    ValueError,
    ImportError,
    EOFError,
    pickle.UnpicklingError,
    # Unpickling a class that no longer exists in its module.
    AttributeError,
)

WRITABLE_EXTENSIONS: tuple[str, ...] = tuple(_WRITERS)
"""File extensions that :func:`save_dataframe` understands."""


@dataclass(frozen=True)
class DataSource:
    """Where a DataFrame came from and how to load it again.

    Attributes
    ----------
    path : pathlib.Path
        The file that was read.
    reader : str
        Name of the top-level ``pandas`` reader, e.g. ``"read_csv"``.
    kwargs : Mapping
        Extra keyword arguments passed to the reader.
    """

    path: Path
    reader: str
    kwargs: Mapping[str, Any] = field(default_factory=dict)

    def read(self) -> pd.DataFrame:
        """Load the file into a DataFrame.

        Raises
        ------
        DataIOError
            If the file is missing, malformed, needs an optional
            dependency that is not installed, or (for pickles) holds
            something other than a DataFrame.
        """
        try:
            data = getattr(pd, self.reader)(self.path, **self.kwargs)
        except _READ_ERRORS as exc:
            raise DataIOError(f"Cannot read {self.path}: {exc}") from exc
        if not isinstance(data, pd.DataFrame):
            # Only pickles can hold arbitrary objects (a Series, a list).
            raise DataIOError(
                f"{self.path} contains a {type(data).__name__}, "
                "not a DataFrame."
            )
        return data

    def to_code(self, variable: str = "df") -> str:
        """Return the ``pandas`` statement that loads this source."""
        arguments = format_call_arguments(str(self.path), **self.kwargs)
        return f"{variable} = pd.{self.reader}({arguments})"


def executes_code_on_read(path: Path | str) -> bool:
    """Return whether loading ``path`` can run code stored in the file.

    The GUI asks the user for confirmation before loading such a file.
    """
    return Path(path).suffix.lower() in UNSAFE_EXTENSIONS


def source_for_path(path: Path | str) -> DataSource:
    """Return the :class:`DataSource` able to read ``path``.

    Raises
    ------
    DataIOError
        If the file extension is not supported.
    """
    path = Path(path)
    try:
        reader, kwargs = _READERS[path.suffix.lower()]
    except KeyError:
        raise DataIOError(
            f"Unsupported file type {path.suffix!r}. "
            f"Supported: {', '.join(READABLE_EXTENSIONS)}"
        ) from None
    return DataSource(path=path, reader=reader, kwargs=dict(kwargs))


def load_dataframe(path: Path | str) -> tuple[pd.DataFrame, DataSource]:
    """Read ``path`` and return the data together with its source.

    This does not ask for consent: check :func:`executes_code_on_read`
    first when ``path`` comes from the user.

    Raises
    ------
    DataIOError
        If the file cannot be read.
    """
    source = source_for_path(path)
    return source.read(), source


def save_dataframe(frame: pd.DataFrame, path: Path | str) -> None:
    """Write ``frame`` to ``path``, choosing the format by extension.

    Raises
    ------
    DataIOError
        If the extension is unsupported or the file cannot be written.
    """
    path = Path(path)
    try:
        writer, kwargs = _WRITERS[path.suffix.lower()]
    except KeyError:
        raise DataIOError(
            f"Unsupported file type {path.suffix!r}. "
            f"Supported: {', '.join(WRITABLE_EXTENSIONS)}"
        ) from None
    try:
        getattr(frame, writer)(path, **kwargs)
    except (OSError, ValueError, ImportError) as exc:
        raise DataIOError(f"Cannot write {path}: {exc}") from exc
