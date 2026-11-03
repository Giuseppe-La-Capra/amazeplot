"""The editing session: current data, applied steps and undo/redo.

:class:`DataSession` is the single source of truth for the GUI. It is
free of any Qt dependency; views register a callback with
:meth:`DataSession.subscribe` and redraw when it fires.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import pandas as pd

from amazeplot.core.errors import SessionError
from amazeplot.core.io import DataSource
from amazeplot.core.operation import Operation

Listener = Callable[[], None]


@dataclass(frozen=True)
class Step:
    """One applied operation together with its resolved parameters."""

    operation: Operation
    params: Mapping[str, Any]

    @property
    def label(self) -> str:
        """Return the operation label, for display purposes."""
        return self.operation.label

    def to_code(self, variable: str = "df") -> str:
        """Return the Python statement equivalent to this step."""
        return self.operation.to_code(self.params, variable)


class DataSession:
    """Hold the loaded data and the history of applied operations.

    Every step stores the DataFrame it produced, so undo and redo are
    instantaneous and never re-run pandas code. Thanks to pandas
    copy-on-write, unchanged columns are shared between snapshots.
    """

    def __init__(self) -> None:
        self._source: DataSource | None = None
        self._frames: list[pd.DataFrame] = []
        self._steps: list[Step] = []
        self._redo_stack: list[tuple[Step, pd.DataFrame]] = []
        self._listeners: list[Listener] = []

    # -- State -----------------------------------------------------------

    @property
    def has_data(self) -> bool:
        """Return whether a DataFrame has been loaded."""
        return bool(self._frames)

    @property
    def frame(self) -> pd.DataFrame | None:
        """Return the current DataFrame, or ``None`` before loading."""
        return self._frames[-1] if self._frames else None

    @property
    def source(self) -> DataSource | None:
        """Return the source of the loaded data, if known."""
        return self._source

    @property
    def steps(self) -> tuple[Step, ...]:
        """Return the applied steps, oldest first."""
        return tuple(self._steps)

    @property
    def can_undo(self) -> bool:
        """Return whether :meth:`undo` would do anything."""
        return bool(self._steps)

    @property
    def can_redo(self) -> bool:
        """Return whether :meth:`redo` would do anything."""
        return bool(self._redo_stack)

    # -- Mutations -------------------------------------------------------

    def load(
        self, frame: pd.DataFrame, source: DataSource | None = None
    ) -> None:
        """Start a new session from ``frame``, discarding all history."""
        self._source = source
        self._frames = [frame]
        self._steps = []
        self._redo_stack = []
        self._notify()

    def apply(
        self, operation: Operation, params: Mapping[str, Any]
    ) -> pd.DataFrame:
        """Apply ``operation`` to the current data and record the step.

        On failure the session is left unchanged.

        Returns
        -------
        pandas.DataFrame
            The new current DataFrame.

        Raises
        ------
        SessionError
            If no data has been loaded.
        OperationError
            If the operation fails.
        """
        current = self._require_frame()
        resolved = operation.resolve_params(params, current.columns.tolist())
        result = operation.execute(current, resolved)
        self._steps.append(Step(operation, resolved))
        self._frames.append(result)
        self._redo_stack.clear()
        self._notify()
        return result

    def undo(self) -> None:
        """Revert the most recent step.

        Raises
        ------
        SessionError
            If there is nothing to undo.
        """
        if not self.can_undo:
            raise SessionError("Nothing to undo.")
        self._redo_stack.append((self._steps.pop(), self._frames.pop()))
        self._notify()

    def redo(self) -> None:
        """Re-apply the most recently undone step.

        Raises
        ------
        SessionError
            If there is nothing to redo.
        """
        if not self.can_redo:
            raise SessionError("Nothing to redo.")
        step, frame = self._redo_stack.pop()
        self._steps.append(step)
        self._frames.append(frame)
        self._notify()

    # -- Observers -------------------------------------------------------

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        """Call ``listener`` after every change of state.

        Returns
        -------
        callable
            A function that removes the subscription when called.
        """
        self._listeners.append(listener)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    def _require_frame(self) -> pd.DataFrame:
        frame = self.frame
        if frame is None:
            raise SessionError("Load a dataset first.")
        return frame
