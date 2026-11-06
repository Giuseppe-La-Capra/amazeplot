"""Panel under the table: details of the selected column and row."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from amazeplot.core.summary import Fields, Sections

_HINT = "Select a cell, a row or a column to see its details."
_HEADERS = ("", "")
_NAME_WIDTH = 160


class InfoPanel(QWidget):
    """Two side-by-side lists: the selected column and the selected row.

    The panel only displays :mod:`amazeplot.core.summary` sections; the
    Data tab decides what to summarise.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._column = self._make_tree("Column")
        self._row = self._make_tree("Row")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._column)
        layout.addWidget(self._row)
        self.clear()

    def show_details(self, column: Sections, row: Sections) -> None:
        """Display the given column and row summaries."""
        self._fill(self._column, column)
        self._fill(self._row, row)

    def clear(self) -> None:
        """Show the hint that explains how to use the panel."""
        hint: Sections = {_HINT: []}
        self._fill(self._column, hint)
        self._fill(self._row, hint)

    def column_fields(self) -> dict[str, str]:
        """Return the column details as ``{name: value}`` (for tests)."""
        return _fields(self._column)

    def row_fields(self) -> dict[str, str]:
        """Return the row details as ``{name: value}`` (for tests)."""
        return _fields(self._row)

    @staticmethod
    def _make_tree(title: str) -> QTreeWidget:
        tree = QTreeWidget()
        tree.setColumnCount(len(_HEADERS))
        tree.setHeaderLabels([title, ""])
        tree.setColumnWidth(0, _NAME_WIDTH)
        tree.setRootIsDecorated(False)
        return tree

    @staticmethod
    def _fill(tree: QTreeWidget, sections: Sections) -> None:
        tree.clear()
        for title, fields in sections.items():
            section = QTreeWidgetItem(tree, [title])
            font = section.font(0)
            font.setBold(True)
            section.setFont(0, font)
            section.setFirstColumnSpanned(True)
            _add_fields(section, fields)
        tree.expandAll()


def _add_fields(section: QTreeWidgetItem, fields: Fields) -> None:
    for name, value in fields:
        item = QTreeWidgetItem(section, [name, value])
        item.setToolTip(1, value)


def _fields(tree: QTreeWidget) -> dict[str, str]:
    values = {}
    for row in range(tree.topLevelItemCount()):
        section = tree.topLevelItem(row)
        for child in range(section.childCount()):
            item = section.child(child)
            values[item.text(0)] = item.text(1)
    return values
