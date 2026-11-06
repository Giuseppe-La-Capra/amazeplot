"""Searchable tree listing every registered action."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from amazeplot.core.action import Action
from amazeplot.core.registry import ActionRegistry

_KEY_ROLE = Qt.ItemDataRole.UserRole


class ActionsPanel(QWidget):
    """Actions grouped by category, filtered by a search box.

    Activating an action (double click or Enter) emits
    :attr:`action_requested` with the :class:`Action`.

    Parameters
    ----------
    registry : ActionRegistry
        The actions to list.
    parent : QWidget, optional
        Parent widget.
    """

    action_requested = Signal(object)

    def __init__(
        self, registry: ActionRegistry, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._registry = registry

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search actions...")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self.set_filter)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.itemActivated.connect(self._on_item_activated)
        self._populate()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._search)
        layout.addWidget(self._tree)

    def set_filter(self, text: str) -> None:
        """Show only actions whose label, key or text contain ``text``."""
        needle = text.strip().lower()
        for row in range(self._tree.topLevelItemCount()):
            category = self._tree.topLevelItem(row)
            visible_children = 0
            for child_row in range(category.childCount()):
                child = category.child(child_row)
                action = self._registry.get(child.data(0, _KEY_ROLE))
                hidden = bool(needle) and needle not in _search_text(action)
                child.setHidden(hidden)
                visible_children += not hidden
            category.setHidden(visible_children == 0)

    def visible_action_keys(self) -> list[str]:
        """Return the keys of the actions currently shown."""
        keys = []
        for row in range(self._tree.topLevelItemCount()):
            category = self._tree.topLevelItem(row)
            for child_row in range(category.childCount()):
                child = category.child(child_row)
                if not child.isHidden():
                    keys.append(child.data(0, _KEY_ROLE))
        return keys

    def _populate(self) -> None:
        for category, actions in self._registry.by_category().items():
            parent = QTreeWidgetItem(self._tree, [category])
            parent.setFlags(Qt.ItemFlag.ItemIsEnabled)
            for action in actions:
                item = QTreeWidgetItem(parent, [action.label])
                item.setData(0, _KEY_ROLE, action.key)
                item.setToolTip(0, action.description)
        self._tree.expandAll()

    def _on_item_activated(self, item: QTreeWidgetItem, column: int) -> None:
        key = item.data(0, _KEY_ROLE)
        if key is not None:
            self.action_requested.emit(self._registry.get(key))


def _search_text(action: Action) -> str:
    """Return the lowercase text matched against the search box."""
    return " ".join(
        (action.category, action.label, action.key, action.description)
    ).lower()
