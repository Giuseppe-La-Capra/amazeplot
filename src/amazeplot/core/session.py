"""The editing session: data, applied steps, plot layers and history.

:class:`DataSession` is the single source of truth for the GUI. It is
free of any Qt dependency; views register a callback with
:meth:`DataSession.subscribe` and redraw when it fires.

The state is a sequence of immutable snapshots. Every change (a data
step, adding or removing a plot layer) pushes a new snapshot, so one
undo/redo history covers both data and plots.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from typing import Any

import pandas as pd

from amazeplot.core.action import Action
from amazeplot.core.errors import SessionError
from amazeplot.core.io import DataSource
from amazeplot.core.operation import Operation
from amazeplot.core.plotting import Layer, PlotCall

Listener = Callable[[], None]

LAYER_CHECK_ROWS = 1_000
"""Rows used to test-draw a new plot layer before accepting it.

Drawing the whole of a large table only to detect a wrong column type or
colour would take seconds; the first rows reveal those mistakes.
"""


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


@dataclass(frozen=True, eq=False)
class _Snapshot:
    """The complete, immutable state of a session at one point."""

    frame: pd.DataFrame
    steps: tuple[Step, ...] = ()
    layers: tuple[Layer, ...] = ()


class DataSession:
    """Hold the loaded data, the applied steps and the plot layers.

    Every snapshot keeps the DataFrame it produced, so undo and redo are
    instantaneous and never re-run pandas code. Thanks to pandas
    copy-on-write, unchanged columns are shared between snapshots, and
    plot-only changes share the same DataFrame object.
    """

    def __init__(self) -> None:
        self._source: DataSource | None = None
        self._history: list[_Snapshot] = []
        self._redo_stack: list[_Snapshot] = []
        self._listeners: list[Listener] = []

    # -- State -----------------------------------------------------------

    @property
    def has_data(self) -> bool:
        """Return whether a DataFrame has been loaded."""
        return bool(self._history)

    @property
    def frame(self) -> pd.DataFrame | None:
        """Return the current DataFrame, or ``None`` before loading."""
        return self._history[-1].frame if self._history else None

    @property
    def source(self) -> DataSource | None:
        """Return the source of the loaded data, if known."""
        return self._source

    @property
    def steps(self) -> tuple[Step, ...]:
        """Return the applied data steps, oldest first."""
        return self._history[-1].steps if self._history else ()

    @property
    def layers(self) -> tuple[Layer, ...]:
        """Return the plot layers, in drawing order."""
        return self._history[-1].layers if self._history else ()

    @property
    def can_undo(self) -> bool:
        """Return whether :meth:`undo` would do anything."""
        return len(self._history) > 1

    @property
    def can_redo(self) -> bool:
        """Return whether :meth:`redo` would do anything."""
        return bool(self._redo_stack)

    # -- Data ------------------------------------------------------------

    def load(
        self, frame: pd.DataFrame, source: DataSource | None = None
    ) -> None:
        """Start a new session from ``frame``, discarding all history."""
        self._source = source
        self._history = [_Snapshot(frame)]
        self._redo_stack = []
        self._notify()

    def apply(
        self, operation: Operation, params: Mapping[str, Any]
    ) -> pd.DataFrame:
        """Apply ``operation`` to the current data and record the step.

        On failure the session is left unchanged. Plot layers are kept;
        if they no longer fit the new data, drawing them reports it.

        Returns
        -------
        pandas.DataFrame
            The new current DataFrame.

        Raises
        ------
        SessionError
            If no data has been loaded.
        ParameterError, OperationError
            If the operation fails.
        """
        current = self._current()
        resolved = operation.resolve_params(
            params, current.frame.columns.tolist()
        )
        result = operation.execute(current.frame, resolved)
        step = Step(operation, resolved)
        self._push(
            replace(current, frame=result, steps=(*current.steps, step))
        )
        return result

    def perform(self, action: Action, params: Mapping[str, Any]) -> None:
        """Apply a data operation or add a plot layer, by action type.

        Raises
        ------
        SessionError
            If no data has been loaded.
        ActionError
            If the action fails; the session is left unchanged.
        TypeError
            If ``action`` is neither an operation nor a plot call.
        """
        if isinstance(action, Operation):
            self.apply(action, params)
        elif isinstance(action, PlotCall):
            self.add_layer(action, params)
        else:
            raise TypeError(f"Unsupported action type {type(action)!r}")

    # -- Plot layers -----------------------------------------------------

    def add_layer(self, call: PlotCall, params: Mapping[str, Any]) -> Layer:
        """Add a plot layer drawn by ``call`` on top of the others.

        Follow-up layers the call asks for (e.g. a colour bar after a
        heatmap) are added right after it, as separate layers. The whole
        addition is one undo step.

        Each call is first drawn on a scratch figure, with the first
        :data:`LAYER_CHECK_ROWS` rows, so a failing layer is not added.
        A problem that only shows up further down the table is reported
        when the figure is drawn.

        Returns
        -------
        Layer
            The layer drawn by ``call`` (not its follow-ups).

        Raises
        ------
        SessionError
            If no data has been loaded.
        ParameterError, PlotError
            If the parameters are invalid or drawing fails.
        """
        current = self._current()
        columns = current.frame.columns.tolist()
        sample = current.frame.head(LAYER_CHECK_ROWS)
        resolved = call.resolve_params(params, columns)
        call.check(sample, resolved, current.layers)
        layer = Layer(call, resolved)
        layers = (*current.layers, layer)
        for follow_call, follow_params in call.follow_up_layers(resolved):
            follow_resolved = follow_call.resolve_params(
                follow_params, columns
            )
            follow_call.check(sample, follow_resolved, layers)
            layers = (*layers, Layer(follow_call, follow_resolved))
        self._push(replace(current, layers=layers))
        return layer

    def remove_layer(self, index: int) -> None:
        """Remove the plot layer at position ``index``.

        Raises
        ------
        SessionError
            If there is no layer at ``index``.
        """
        current = self._current()
        if not 0 <= index < len(current.layers):
            raise SessionError(f"There is no plot layer {index + 1}.")
        layers = tuple(
            layer
            for position, layer in enumerate(current.layers)
            if position != index
        )
        self._push(replace(current, layers=layers))

    def clear_layers(self) -> None:
        """Remove every plot layer.

        Raises
        ------
        SessionError
            If there are no layers.
        """
        current = self._current()
        if not current.layers:
            raise SessionError("There are no plot layers.")
        self._push(replace(current, layers=()))

    # -- History ---------------------------------------------------------

    def undo(self) -> None:
        """Revert the most recent change (data step or plot layer).

        Raises
        ------
        SessionError
            If there is nothing to undo.
        """
        if not self.can_undo:
            raise SessionError("Nothing to undo.")
        self._redo_stack.append(self._history.pop())
        self._notify()

    def redo(self) -> None:
        """Re-apply the most recently undone change.

        Raises
        ------
        SessionError
            If there is nothing to redo.
        """
        if not self.can_redo:
            raise SessionError("Nothing to redo.")
        self._history.append(self._redo_stack.pop())
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

    # -- Helpers ---------------------------------------------------------

    def _push(self, snapshot: _Snapshot) -> None:
        self._history.append(snapshot)
        self._redo_stack.clear()
        self._notify()

    def _notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    def _current(self) -> _Snapshot:
        if not self._history:
            raise SessionError("Load a dataset first.")
        return self._history[-1]
