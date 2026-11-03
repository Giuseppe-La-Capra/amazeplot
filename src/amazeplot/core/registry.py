"""A catalogue of the operations available in the application."""

from __future__ import annotations

from collections.abc import Iterable, Iterator

from amazeplot.core.operation import Operation


class OperationRegistry:
    """Ordered collection of operations, indexed by :attr:`Operation.key`.

    The registry is a plain object passed to whoever needs it (no global
    state), which keeps tests isolated and makes plugins easy to add.

    Parameters
    ----------
    operations : iterable of Operation, optional
        Operations to register immediately.
    """

    def __init__(self, operations: Iterable[Operation] = ()) -> None:
        self._operations: dict[str, Operation] = {}
        for operation in operations:
            self.register(operation)

    def register(self, operation: Operation) -> None:
        """Add ``operation`` to the registry.

        Raises
        ------
        ValueError
            If an operation with the same key is already registered.
        """
        if operation.key in self._operations:
            raise ValueError(f"Duplicate operation key {operation.key!r}")
        self._operations[operation.key] = operation

    def get(self, key: str) -> Operation:
        """Return the operation registered under ``key``.

        Raises
        ------
        KeyError
            If no operation has that key.
        """
        try:
            return self._operations[key]
        except KeyError:
            raise KeyError(f"Unknown operation {key!r}") from None

    def by_category(self) -> dict[str, list[Operation]]:
        """Group operations by category, preserving registration order."""
        groups: dict[str, list[Operation]] = {}
        for operation in self:
            groups.setdefault(operation.category, []).append(operation)
        return groups

    def __contains__(self, key: object) -> bool:
        """Return whether an operation is registered under ``key``."""
        return key in self._operations

    def __iter__(self) -> Iterator[Operation]:
        """Iterate over operations in registration order."""
        return iter(self._operations.values())

    def __len__(self) -> int:
        """Return the number of registered operations."""
        return len(self._operations)
