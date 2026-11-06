"""Plot calls: matplotlib ``Axes`` methods exposed as actions.

A figure is a stack of :class:`Layer` objects drawn in order on a single
``matplotlib.axes.Axes``. Every layer is one call such as
``ax.scatter(df['age'], df['score'], alpha=0.5)`` or
``ax.set_title('Scores')``.

Like data operations, plot calls build their arguments **once**. The
same arguments are then either resolved against the DataFrame and
passed to matplotlib, or rendered as source code, so the exported
script draws exactly what the GUI shows.

This module never imports :mod:`matplotlib.pyplot`. pyplot keeps global
state (the "current figure"), so drawing happens on plain
:class:`matplotlib.figure.Figure` objects. Only generated scripts use
pyplot.
"""

from __future__ import annotations

import abc
import warnings
from collections.abc import Callable, Hashable, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from amazeplot.core.action import Action, Params, equals_default
from amazeplot.core.errors import PlotError
from amazeplot.core.parameters import Parameter, ParameterKind, is_empty

AXES_VARIABLE = "ax"
"""Name of the ``Axes`` variable in generated code."""

ExtraKwargs = Callable[[Params], dict[str, Any]]
"""Computes keyword arguments that do not come from a single widget."""

MATPLOTLIB_API_URL = (
    "https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.{}.html"
)
"""Documentation page of an ``Axes`` method, by method name."""


@dataclass(frozen=True)
class ColumnRef:
    """Placeholder for ``frame[label]`` inside plot-call arguments.

    Attributes
    ----------
    label : Hashable
        Column label.
    dropna : bool
        Whether missing values are removed (``frame[label].dropna()``).
    """

    label: Hashable
    dropna: bool = False

    def resolve(self, frame: pd.DataFrame) -> pd.Series:
        """Return the referenced column of ``frame``."""
        series = frame[self.label]
        return series.dropna() if self.dropna else series

    def to_code(self, variable: str) -> str:
        """Return the source expression selecting the column."""
        code = f"{variable}[{self.label!r}]"
        return code + ".dropna()" if self.dropna else code


@dataclass(frozen=True)
class NumericFrameRef:
    """Placeholder for the numeric columns of the whole DataFrame."""

    def resolve(self, frame: pd.DataFrame) -> pd.DataFrame:
        """Return the numeric columns of ``frame``."""
        return frame.select_dtypes("number")

    def to_code(self, variable: str) -> str:
        """Return the source expression selecting the numeric columns."""
        return f"{variable}.select_dtypes('number')"


_Reference = ColumnRef | NumericFrameRef


def resolve_argument(value: Any, frame: pd.DataFrame) -> Any:
    """Replace references in ``value`` with data from ``frame``."""
    if isinstance(value, _Reference):
        return value.resolve(frame)
    if isinstance(value, list):
        return [resolve_argument(item, frame) for item in value]
    return value


def render_argument(value: Any, variable: str) -> str:
    """Return ``value`` as source code, rendering references."""
    if isinstance(value, _Reference):
        return value.to_code(variable)
    if isinstance(value, list):
        items = ", ".join(render_argument(item, variable) for item in value)
        return f"[{items}]"
    return repr(value)


@dataclass(frozen=True)
class PlotCall(Action):
    """Base class of every action that draws on an ``Axes``.

    Subclasses implement :meth:`_draw` and :meth:`to_code`. Callers use
    :meth:`draw`, which converts matplotlib failures into
    :class:`PlotError`.
    """

    def draw(self, frame: pd.DataFrame, params: Params, axes: Axes) -> None:
        """Draw on ``axes`` using already-resolved parameters.

        Raises
        ------
        PlotError
            If matplotlib rejects the call (wrong data type, invalid
            colour, missing column, ...).
        """
        try:
            self._draw(frame, params, axes)
        except Exception as exc:
            # Deliberately broad: this is the boundary where arbitrary
            # matplotlib/pandas failures become user-facing messages.
            raise PlotError(f"{self.label} failed: {exc}") from exc

    def check(self, frame: pd.DataFrame, params: Params) -> None:
        """Draw once on a scratch figure to detect errors early.

        Raises
        ------
        PlotError
            If drawing fails.
        """
        with warnings.catch_warnings():
            # The scratch axes are empty, so warnings such as "no
            # artists with labels" for a legend are meaningless here.
            warnings.simplefilter("ignore")
            self.draw(frame, params, Figure().add_subplot())

    @abc.abstractmethod
    def _draw(self, frame: pd.DataFrame, params: Params, axes: Axes) -> None:
        """Draw using already-resolved parameters."""


@dataclass(frozen=True)
class AxesCall(PlotCall):
    """A plot call that invokes one ``matplotlib.axes.Axes`` method.

    Parameters named in :attr:`positional` are passed positionally, in
    that order, and skipped when empty. All other parameters become
    keyword arguments and, as for data operations, are omitted when
    empty or equal to their default. ``COLUMN`` values become
    ``df[column]`` and ``COLUMNS`` values a list of them.

    Attributes
    ----------
    method : str
        Name of the ``Axes`` method to call.
    positional : tuple of str
        Names of the parameters passed positionally.
    numeric_frame : bool
        Pass the numeric columns of the whole frame as first argument.
    dropna : bool
        Drop missing values from every referenced column (needed by
        ``hist`` and ``boxplot``, which fail on NaN).
    extra_kwargs : callable, optional
        Adds computed keyword arguments, e.g. legend labels taken from
        the selected column names.
    """

    method: str = ""
    positional: tuple[str, ...] = ()
    numeric_frame: bool = False
    dropna: bool = False
    extra_kwargs: ExtraKwargs | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        """Check the method and the positional parameter names."""
        super().__post_init__()
        if not callable(getattr(Axes, self.method, None)):
            raise ValueError(f"Axes has no method {self.method!r}")
        for name in self.positional:
            self.parameter(name)  # Raises KeyError for unknown names.

    @property
    def documentation_url(self) -> str:
        """Return the matplotlib documentation page of :attr:`method`."""
        return MATPLOTLIB_API_URL.format(self.method)

    def build_arguments(
        self, params: Params
    ) -> tuple[list[Any], dict[str, Any]]:
        """Return the positional and keyword arguments, with references.

        The result still contains :class:`ColumnRef` placeholders. Use
        :func:`resolve_argument` to obtain the data, or
        :func:`render_argument` to obtain source code.
        """
        args: list[Any] = [NumericFrameRef()] if self.numeric_frame else []
        kwargs: dict[str, Any] = {}
        for name in self.positional:
            value = params.get(name)
            if not is_empty(value):
                args.append(self._wrap(self.parameter(name), value))
        for param in self.parameters:
            if param.name in self.positional:
                continue
            value = params.get(param.name, param.default)
            if is_empty(value) or equals_default(value, param.default):
                continue
            kwargs[param.name] = self._wrap(param, value)
        if self.extra_kwargs is not None:
            kwargs.update(self.extra_kwargs(params))
        return args, kwargs

    def _wrap(self, param: Parameter, value: Any) -> Any:
        """Turn column labels into :class:`ColumnRef` placeholders."""
        if param.kind is ParameterKind.COLUMN:
            return ColumnRef(value, self.dropna)
        if param.kind is ParameterKind.COLUMNS:
            return [ColumnRef(label, self.dropna) for label in value]
        return value

    def _draw(self, frame: pd.DataFrame, params: Params, axes: Axes) -> None:
        args, kwargs = self.build_arguments(params)
        getattr(axes, self.method)(
            *resolve_argument(args, frame),
            **{
                name: resolve_argument(value, frame)
                for name, value in kwargs.items()
            },
        )

    def to_code(self, params: Params, variable: str = "df") -> str:
        """Return ``ax.method(...)`` source code."""
        args, kwargs = self.build_arguments(params)
        parts = [render_argument(value, variable) for value in args]
        parts += [
            f"{name}={render_argument(value, variable)}"
            for name, value in kwargs.items()
        ]
        return f"{AXES_VARIABLE}.{self.method}({', '.join(parts)})"


@dataclass(frozen=True)
class Layer:
    """One plot call on the figure, with its resolved parameters."""

    call: PlotCall
    params: Mapping[str, Any]

    @property
    def label(self) -> str:
        """Return the plot-call label, for display purposes."""
        return self.call.label

    def draw(self, frame: pd.DataFrame, axes: Axes) -> None:
        """Draw this layer on ``axes``; raises :class:`PlotError`."""
        self.call.draw(frame, self.params, axes)

    def to_code(self, variable: str = "df") -> str:
        """Return the Python statement equivalent to this layer."""
        return self.call.to_code(self.params, variable)


def render_layers(
    layers: Iterable[Layer], frame: pd.DataFrame, axes: Axes
) -> None:
    """Draw ``layers`` in order on ``axes``.

    Raises
    ------
    PlotError
        From the first layer that cannot be drawn. Layers before it
        stay drawn.
    """
    for layer in layers:
        layer.draw(frame, axes)
