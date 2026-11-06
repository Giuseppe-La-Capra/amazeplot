"""Window that shows the help pages with a table of contents."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSplitter,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from amazeplot.gui.help_pages import HelpPage, category_key

WINDOW_TITLE = "amazeplot Help"
_KEY_ROLE = Qt.ItemDataRole.UserRole
_DEFAULT_SIZE = (960, 680)
_CONTENTS_WIDTH = 240


class HelpWindow(QWidget):
    """Table of contents on the left, the selected page on the right.

    It is a separate top-level window, so it stays usable while a tool's
    dialog is open.

    Parameters
    ----------
    pages : sequence of HelpPage
        Pages in table-of-contents order (see ``build_help_pages``).
        Pages with a category are listed under that category's page.
    parent : QWidget, optional
        Parent widget.
    """

    def __init__(
        self, pages: Sequence[HelpPage], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle(WINDOW_TITLE)
        self._pages = {page.key: page for page in pages}
        self._items: dict[str, QTreeWidgetItem] = {}

        self._contents = QTreeWidget()
        self._contents.setHeaderHidden(True)
        self._contents.currentItemChanged.connect(self._on_item_changed)
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._populate(pages)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._contents)
        splitter.addWidget(self._browser)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([_CONTENTS_WIDTH, _DEFAULT_SIZE[0]])
        layout = QHBoxLayout(self)
        layout.addWidget(splitter)
        self.resize(*_DEFAULT_SIZE)

        if pages:
            self.show_page(pages[0].key)

    def show_page(self, key: str) -> None:
        """Select and display the page called ``key``.

        Raises
        ------
        KeyError
            If there is no such page.
        """
        self._contents.setCurrentItem(self._items[key])

    def current_key(self) -> str | None:
        """Return the key of the displayed page."""
        item = self._contents.currentItem()
        return None if item is None else item.data(0, _KEY_ROLE)

    def current_text(self) -> str:
        """Return the displayed page as plain text (useful for tests)."""
        return self._browser.toPlainText()

    def page_keys(self) -> list[str]:
        """Return every page key in table-of-contents order."""
        return list(self._items)

    def _populate(self, pages: Sequence[HelpPage]) -> None:
        for page in pages:
            if page.category is None:
                item = QTreeWidgetItem(self._contents, [page.title])
            else:
                parent = self._items[category_key(page.category)]
                item = QTreeWidgetItem(parent, [page.title])
            item.setData(0, _KEY_ROLE, page.key)
            self._items[page.key] = item
        self._contents.expandAll()

    def _on_item_changed(
        self, current: QTreeWidgetItem | None, previous: object
    ) -> None:
        if current is not None:
            page = self._pages[current.data(0, _KEY_ROLE)]
            self._browser.setHtml(page.html)
