"""GUI-independent model layer of amazeplot.

Nothing in this package may import Qt or :mod:`matplotlib.pyplot`.
Everything here can be used from a script, a notebook or the test-suite
without a display.
"""

from amazeplot.core.action import Action
from amazeplot.core.codegen import generate_script
from amazeplot.core.errors import (
    ActionError,
    AmazeplotError,
    DataIOError,
    OperationError,
    ParameterError,
    PlotError,
    SessionError,
)
from amazeplot.core.io import DataSource, load_dataframe, save_dataframe
from amazeplot.core.operation import MethodOperation, Operation
from amazeplot.core.parameters import Parameter, ParameterKind
from amazeplot.core.plotting import AxesCall, Layer, PlotCall
from amazeplot.core.registry import ActionRegistry
from amazeplot.core.session import DataSession, Step

__all__ = [
    "Action",
    "ActionError",
    "ActionRegistry",
    "AmazeplotError",
    "AxesCall",
    "DataIOError",
    "DataSession",
    "DataSource",
    "Layer",
    "MethodOperation",
    "Operation",
    "OperationError",
    "Parameter",
    "ParameterError",
    "ParameterKind",
    "PlotCall",
    "PlotError",
    "SessionError",
    "Step",
    "generate_script",
    "load_dataframe",
    "save_dataframe",
]
