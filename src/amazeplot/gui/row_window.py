"""Which rows of the DataFrame the table shows.

Large tables are never handed to Qt whole: the Data tab shows a window
of consecutive rows that the user moves with the bar above the table.
This module holds the window arithmetic; it is Qt-free so it can be
tested on its own.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

PAGE_SIZES: tuple[int, ...] = (100, 1_000, 10_000, 100_000)
"""Choices offered for the number of rows shown at once."""

DEFAULT_PAGE_SIZE = 1_000
"""Rows shown at once until the user picks another page size."""

_RANGE_DASH = "\N{EN DASH}"


@dataclass(frozen=True)
class RowWindow:
    """A range of row positions: ``start`` (0-based) and ``size`` rows.

    Methods that depend on the table length take ``total``, the number
    of rows of the DataFrame, so one window can be reused across data
    steps that change the length.
    """

    start: int = 0
    size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        """Reject a negative start or an empty window."""
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")
        if self.size < 1:
            raise ValueError(f"size must be >= 1, got {self.size}")

    def clamped(self, total: int) -> RowWindow:
        """Return the window moved back inside a table of ``total`` rows.

        The start never goes past the last row, so after a data step
        that shortens the table the view stays as close as possible to
        where the user was.
        """
        last_row = max(total - 1, 0)
        return replace(self, start=min(self.start, last_row))

    def stop(self, total: int) -> int:
        """Return the position after the last shown row (exclusive)."""
        return min(self.start + self.size, total)

    def has_previous(self) -> bool:
        """Return whether rows exist before the window."""
        return self.start > 0

    def has_next(self, total: int) -> bool:
        """Return whether rows exist after the window."""
        return self.start + self.size < total

    def previous(self) -> RowWindow:
        """Return the window one page earlier (stopping at row 0)."""
        return replace(self, start=max(self.start - self.size, 0))

    def next(self, total: int) -> RowWindow:
        """Return the window one page later, if there are more rows."""
        if not self.has_next(total):
            return self
        return replace(self, start=self.start + self.size)

    def describe(self, total: int) -> str:
        """Return the rows shown, e.g. rows 1 to 1,000 of 2,500 (1-based)."""
        if total == 0:
            return "No rows"
        first, last = self.start + 1, self.stop(total)
        return f"Showing rows {first:,}{_RANGE_DASH}{last:,} of {total:,}"
