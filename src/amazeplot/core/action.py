"""The :class:`Action` base class shared by every toolbox entry.

An action is anything the user can pick from the toolbox and configure
in a form: a pandas data operation
(:class:`~amazeplot.core.operation.Operation`) or a matplotlib plot call
(:class:`~amazeplot.core.plotting.PlotCall`). Both share the same
metadata, parameter handling and code generation, so the GUI treats
them uniformly.
"""

from __future__ import annotations

import abc
from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from amazeplot.core.errors import ParameterError
from amazeplot.core.parameters import Parameter

Params = Mapping[str, Any]
"""Parameter values keyed by :attr:`Parameter.name`."""


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


def equals_default(value: Any, default: Any) -> bool:
    """Return whether ``value`` equals ``default`` (``0 != False``)."""
    return type(value) is type(default) and value == default


@dataclass(frozen=True)
class Action(abc.ABC):
    """Base class of every entry offered in the toolbox.

    Attributes
    ----------
    key : str
        Unique identifier, used by the registry.
    label : str
        Human-readable name shown in the GUI.
    category : str
        Group under which the action is listed.
    description : str
        One or two sentences shown in the action dialog.
    parameters : tuple of Parameter
        Inputs of the action, in display order.
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
            If the action has no such parameter.
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
            Column labels of the DataFrame the action will use.

        Returns
        -------
        dict
            A value for every parameter, in declaration order.

        Raises
        ------
        ParameterError
            If a value is missing or invalid, or a name is unknown.
        """
        known = {param.name for param in self.parameters}
        unknown = sorted(set(params) - known)
        if unknown:
            raise ParameterError(
                f"{self.label}: unknown parameter(s) {unknown!r}."
            )
        resolved = {}
        for param in self.parameters:
            value = param.coerce(params.get(param.name, param.default))
            param.validate(value, columns)
            resolved[param.name] = value
        return resolved

    @abc.abstractmethod
    def to_code(self, params: Params, variable: str = "df") -> str:
        """Return the Python statement equivalent to this action.

        Parameters
        ----------
        params : Mapping
            Resolved parameter values (see :meth:`resolve_params`).
        variable : str, default "df"
            Name of the DataFrame variable in the generated code.

        Returns
        -------
        str
            A single statement, e.g. ``df = df.dropna(how='all')``.
        """
