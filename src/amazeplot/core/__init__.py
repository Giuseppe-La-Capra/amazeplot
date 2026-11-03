"""GUI-independent model layer of amazeplot.

Nothing in this package may import Qt. Everything here can be used from
a script, a notebook or the test-suite without a display.
"""

from amazeplot.core.codegen import generate_script
from amazeplot.core.errors import (
    AmazeplotError,
    DataIOError,
    OperationError,
    ParameterError,
    SessionError,
)
from amazeplot.core.io import DataSource, load_dataframe, save_dataframe
from amazeplot.core.operation import MethodOperation, Operation
from amazeplot.core.parameters import Parameter, ParameterKind
from amazeplot.core.registry import OperationRegistry
from amazeplot.core.session import DataSession, Step

__all__ = [
    "AmazeplotError",
    "DataIOError",
    "DataSession",
    "DataSource",
    "MethodOperation",
    "Operation",
    "OperationError",
    "OperationRegistry",
    "Parameter",
    "ParameterError",
    "ParameterKind",
    "SessionError",
    "Step",
    "generate_script",
    "load_dataframe",
    "save_dataframe",
]
