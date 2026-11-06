import pytest

from amazeplot.gui.help_pages import (
    GETTING_STARTED_KEY,
    build_help_pages,
    category_key,
)
from amazeplot.gui.help_window import HelpWindow
from amazeplot.operations import build_default_registry


@pytest.fixture(scope="module")
def pages():
    return build_help_pages(build_default_registry())


@pytest.fixture
def window(qtbot, pages):
    window = HelpWindow(pages)
    qtbot.addWidget(window)
    return window


def test_opens_on_getting_started(window):
    assert window.current_key() == GETTING_STARTED_KEY
    assert "Getting started" in window.current_text()


def test_contents_follow_page_order(window, pages):
    assert window.page_keys() == [page.key for page in pages]


def test_show_page(window):
    window.show_page("plot_scatter")
    assert window.current_key() == "plot_scatter"
    assert "Scatter" in window.current_text()
    window.show_page(category_key("Clean"))
    assert "Drop missing values" in window.current_text()


def test_unknown_page(window):
    with pytest.raises(KeyError):
        window.show_page("nope")
