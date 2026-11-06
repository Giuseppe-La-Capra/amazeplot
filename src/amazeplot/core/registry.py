"""A catalogue of the actions available in the application."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from amazeplot.core.action import Action


class ActionRegistry:
    """Ordered collection of actions, indexed by :attr:`Action.key`.

    The registry is a plain object passed to whoever needs it (no global
    state), which keeps tests isolated and makes plugins easy to add.

    Parameters
    ----------
    actions : iterable of Action, optional
        Actions to register immediately.
    """

    def __init__(self, actions: Iterable[Action] = ()) -> None:
        self._actions: dict[str, Action] = {}
        for action in actions:
            self.register(action)

    def register(self, action: Action) -> None:
        """Add ``action`` to the registry.

        Raises
        ------
        ValueError
            If an action with the same key is already registered.
        """
        if action.key in self._actions:
            raise ValueError(f"Duplicate action key {action.key!r}")
        self._actions[action.key] = action

    def get(self, key: str) -> Action:
        """Return the action registered under ``key``.

        Raises
        ------
        KeyError
            If no action has that key.
        """
        try:
            return self._actions[key]
        except KeyError:
            raise KeyError(f"Unknown action {key!r}") from None

    def by_category(self) -> dict[str, list[Action]]:
        """Group actions by category, preserving registration order."""
        groups: dict[str, list[Action]] = {}
        for action in self:
            groups.setdefault(action.category, []).append(action)
        return groups

    def __contains__(self, key: object) -> bool:
        """Return whether an action is registered under ``key``."""
        return key in self._actions

    def __iter__(self) -> Iterator[Action]:
        """Iterate over actions in registration order."""
        return iter(self._actions.values())

    def __len__(self) -> int:
        """Return the number of registered actions."""
        return len(self._actions)
