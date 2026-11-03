"""The :class:`Operation` abstraction: one graphical pandas action.

An operation is an :class:`~amazeplot.core.action.Action` that turns a
DataFrame into a new DataFrame. On top of the action metadata it knows
how to transform the data (:meth:`Operation.apply`, or
:meth:`Operation.execute` once parameters are resolved).

Execution and code generation are derived from the *same* keyword
arguments, so the exported script always reproduces what the GUI did.
"""

from __future__ import annotations

import abc
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from amazeplot.core.action import (
    Action,
    Params,
    equals_default,
    format_call_arguments,
)
from amazeplot.core.errors import OperationError
from amazeplot.core.parameters import is_empty

KwargsBuilder = Callable[[Params], dict[str, Any]]
"""Maps resolved parameter values to pandas keyword arguments."""


@dataclass(frozen=True)
class Operation(Action):
    """Base class of every data operation.

    Subclasses implement :meth:`_execute` and :meth:`to_code`. Callers
    use :meth:`apply` (or :meth:`resolve_params` followed by
    :meth:`execute`), which validates parameters and converts pandas
    failures into :class:`OperationError`.
    """

    def apply(self, frame: pd.DataFrame, params: Params) -> pd.DataFrame:
        """Validate ``params`` and run the operation on ``frame``.

        Parameters
        ----------
        frame : pandas.DataFrame
            Input data. It is never mutated.
        params : Mapping
            Raw parameter values, see :meth:`resolve_params`.

        Returns
        -------
        pandas.DataFrame
            The transformed data.

        Raises
        ------
        ParameterError
            If the parameters are invalid.
        OperationError
            If pandas rejects the call.
        """
        resolved = self.resolve_params(params, frame.columns.tolist())
        return self.execute(frame, resolved)

    def execute(self, frame: pd.DataFrame, params: Params) -> pd.DataFrame:
        """Run the operation with parameters already resolved.

        Use this instead of :meth:`apply` when the parameters come from
        :meth:`resolve_params`, so they are not coerced twice.

        Raises
        ------
        OperationError
            If pandas rejects the call.
        """
        try:
            result = self._execute(frame, dict(params))
        except Exception as exc:
            # Deliberately broad: this is the boundary where arbitrary
            # pandas failures (KeyError, TypeError, SyntaxError in query
            # strings, ...) become user-facing messages.
            raise OperationError(f"{self.label} failed: {exc}") from exc
        if not isinstance(result, pd.DataFrame):
            # A programming error in the operation, not a user error.
            raise TypeError(
                f"Operation {self.key!r} returned "
                f"{type(result).__name__}, expected DataFrame"
            )
        return result

    @abc.abstractmethod
    def _execute(
        self, frame: pd.DataFrame, params: dict[str, Any]
    ) -> pd.DataFrame:
        """Transform ``frame`` using already-resolved parameters."""


@dataclass(frozen=True)
class MethodOperation(Operation):
    """An operation that calls one ``DataFrame`` method.

    This covers the vast majority of operations. The parameters are
    forwarded as keyword arguments to ``getattr(frame, method)``. Values
    that are empty or equal to the parameter default are omitted, which
    keeps both the call and the generated code minimal.

    Attributes
    ----------
    method : str
        Name of the ``pandas.DataFrame`` method to call.
    kwargs_builder : callable, optional
        Custom mapping from parameter values to keyword arguments, for
        methods whose arguments do not map one-to-one onto widgets
        (e.g. ``rename(columns={old: new})``).
    then : str, optional
        Name of a no-argument method chained on the result, typically
        ``"reset_index"`` to turn a Series or index back into columns.
    """

    method: str = ""
    kwargs_builder: KwargsBuilder | None = field(default=None, compare=False)
    then: str | None = None

    def __post_init__(self) -> None:
        """Check that ``method`` names a real ``DataFrame`` method."""
        super().__post_init__()
        if not callable(getattr(pd.DataFrame, self.method, None)):
            raise ValueError(f"DataFrame has no method {self.method!r}")

    def build_kwargs(self, params: Params) -> dict[str, Any]:
        """Return the keyword arguments passed to the pandas method."""
        if self.kwargs_builder is not None:
            return self.kwargs_builder(params)
        kwargs = {}
        for param in self.parameters:
            value = params.get(param.name, param.default)
            if is_empty(value) or equals_default(value, param.default):
                continue
            kwargs[param.name] = value
        return kwargs

    def _execute(
        self, frame: pd.DataFrame, params: dict[str, Any]
    ) -> pd.DataFrame:
        result = getattr(frame, self.method)(**self.build_kwargs(params))
        if self.then is not None:
            result = getattr(result, self.then)()
        return result

    def to_code(self, params: Params, variable: str = "df") -> str:
        """Return ``variable = variable.method(...)`` source code."""
        arguments = format_call_arguments(**self.build_kwargs(params))
        code = f"{variable} = {variable}.{self.method}({arguments})"
        if self.then is not None:
            code += f".{self.then}()"
        return code
