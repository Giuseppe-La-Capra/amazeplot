"""Built-in operations shipped with amazeplot.

Each module groups the operations of one GUI category and exposes them
in a module-level ``OPERATIONS`` tuple. :func:`build_default_registry`
collects them all, in the order categories appear in the GUI.
"""

from amazeplot.core.registry import OperationRegistry
from amazeplot.operations import aggregate, clean, select, transform

_MODULES = (select, clean, transform, aggregate)


def build_default_registry() -> OperationRegistry:
    """Return a new registry containing every built-in operation."""
    registry = OperationRegistry()
    for module in _MODULES:
        for operation in module.OPERATIONS:
            registry.register(operation)
    return registry


__all__ = ["build_default_registry"]
