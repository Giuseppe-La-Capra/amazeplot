"""Built-in catalogue of actions shipped with amazeplot.

Each module groups the actions of one toolbox category and exposes them
in a module-level ``ACTIONS`` tuple: data operations (``select``,
``clean``, ``create``, ``transform``, ``aggregate``) and matplotlib
plot calls
(``plot``, ``decorate``). :func:`build_default_registry` collects them
all, in the order categories appear in the GUI.
"""

from amazeplot.core.registry import ActionRegistry
from amazeplot.operations import (
    aggregate,
    clean,
    create,
    decorate,
    plot,
    select,
    transform,
)

_MODULES = (select, clean, create, transform, aggregate, plot, decorate)


def build_default_registry() -> ActionRegistry:
    """Return a new registry containing every built-in action."""
    registry = ActionRegistry()
    for module in _MODULES:
        for action in module.ACTIONS:
            registry.register(action)
    return registry


__all__ = ["build_default_registry"]
