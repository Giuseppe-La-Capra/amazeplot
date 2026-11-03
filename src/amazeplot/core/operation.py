"""The :class:`Operation` abstraction: one graphical pandas action.

An operation knows three things:

* which parameters it needs (:attr:`Operation.parameters`),
* how to transform a DataFrame (:meth:`Operation.apply`, or
  :meth:`Operation.execute` once parameters are resolved),
* how to express that transformation as Python source
  (:meth:`Operation.to_code`).

Execution and code generation are derived from the *same* keyword
arguments, so the exported script always reproduces what the GUI did.
"""

from __future__ import annotations

import abc
from collections.abc import Callable, Hashable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from amazeplot.core.errors import OperationError
from amazeplot.core.parameters import Parameter, is_empty

Params = Mapping[str, Any]
"""Parameter values keyed by :attr:`Parameter.name`."""

KwargsBuilder = Callable[[Params], dict[str, Any]]
"""Maps resolved parameter values to pandas keyword arguments."""


def format_call_arguments(*args: Any, **kwargs: Any) -> str:
    """Format positional and keyword arguments as Python source.

    Parameters
    ----------
    *args : Any
        Positional arguments, rendered with :func:`repr`.
    **kwargs : Any
        Keyword arguments, rendered as ``name=repr(value)``.

    Returns
    -------
    str
        Comma-separated argument list, without parentheses.

    Examples
    --------
    >>> format_call_arguments(["a"], how="any")
    "['a'], how='any'"
    """
    parts = [repr(value) for value in args]
    parts += [f"{name}={value!r}" for name, value in kwargs.items()]
    return ", ".join(parts)


@dataclass(frozen=True)
class Operation(abc.ABC):
    """Base class of every operation exposed in the GUI.

    Subclasses implement :meth:`_execute` and :meth:`to_code`. Callers
    use :meth:`apply` (or :meth:`resolve_params` followed by
    :meth:`execute`), which validates parameters and converts pandas
    failures into :class:`OperationError`.

    Attributes
    ----------
    key : str
        Unique identifier, used by the registry.
    label : str
        Human-readable name shown in the GUI.
    category : str
        Group under which the operation is listed.
    description : str
        One or two sentences shown in the operation dialog.
    parameters : tuple of Parameter
        Inputs of the operation, in display order.
    """

    key: str
    label: str
    category: str
    description: str
    parameters: tuple[Parameter, ...] = ()

    def __post_init__(self) -> None:
        """Reject duplicate parameter names."""
        names = [param.name for param in self.parameters]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate parameter names in {self.key!r}")

    def parameter(self, name: str) -> Parameter:
        """Return the parameter called ``name``.

        Raises
        ------
        KeyError
            If the operation has no such parameter.
        """
        for param in self.parameters:
            if param.name == name:
                return param
        raise KeyError(f"{self.key!r} has no parameter {name!r}")

    def resolve_params(
        self, params: Params, columns: Sequence[Hashable]
    ) -> dict[str, Any]:
        """Fill in defaults, coerce and validate parameter values.

        Parameters
        ----------
        params : Mapping
            Raw values keyed by parameter name. Missing entries take the
            parameter's default.
        columns : Sequence of Hashable
            Column labels of the DataFrame the operation will run on.

        Returns
        -------
        dict
            A value for every parameter, in declaration order.

        Raises
        ------
        ParameterError
            If a value is missing or invalid.
        OperationError
            If ``params`` contains unknown names.
        """
        known = {param.name for param in self.parameters}
        unknown = sorted(set(params) - known)
        if unknown:
            raise OperationError(
                f"{self.label}: unknown parameter(s) {unknown!r}."
            )
        resolved = {}
        for param in self.parameters:
            value = param.coerce(params.get(param.name, param.default))
            param.validate(value, columns)
            resolved[param.name] = value
        return resolved

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
        OperationError
            If the parameters are invalid or pandas rejects the call.
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

    @abc.abstractmethod
    def to_code(self, params: Params, variable: str = "df") -> str:
        """Return Python source equivalent to :meth:`apply`.

        Parameters
        ----------
        params : Mapping
            Resolved parameter values (see :meth:`resolve_params`).
        variable : str, default "df"
            Name of the DataFrame variable in the generated code.

        Returns
        -------
        str
            A single statement such as ``df = df.dropna(how='all')``.
        """


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
            if is_empty(value) or _equals_default(value, param.default):
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


def _equals_default(value: Any, default: Any) -> bool:
    """Compare with the default, treating ``0``/``False`` as distinct."""
    return type(value) is type(default) and value == default
