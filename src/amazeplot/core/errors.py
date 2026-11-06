"""Exception hierarchy of the core layer.

Every error that is caused by user input (bad parameters, a pandas or
matplotlib call that fails on the current data, an unreadable file)
derives from :class:`AmazeplotError`. The GUI catches this base class
and shows the message to the user; any other exception is treated as a
bug.
"""


class AmazeplotError(Exception):
    """Base class for all expected, user-facing errors."""


class ActionError(AmazeplotError):
    """An action (data operation or plot call) could not be performed."""


class ParameterError(ActionError):
    """A parameter value is missing, unknown or invalid."""


class OperationError(ActionError):
    """A data operation could not be applied to the current data."""


class PlotError(ActionError):
    """A plot call could not be drawn with the current data."""


class SessionError(AmazeplotError):
    """The session is not in a state that allows the request."""


class DataIOError(AmazeplotError):
    """A file could not be read or written."""
