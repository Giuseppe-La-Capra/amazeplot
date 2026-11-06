"""Tests of the generated help content (Qt-free)."""

import html
import re

import pytest

from amazeplot.core.examples import EXAMPLE_COLUMNS
from amazeplot.gui.help_pages import (
    CATEGORY_INTROS,
    GETTING_STARTED_KEY,
    GETTING_STARTED_STEPS,
    action_page,
    build_help_pages,
    category_key,
)
from amazeplot.operations import build_default_registry

REGISTRY = build_default_registry()
PAGES = build_help_pages(REGISTRY)


def _text(page_html: str) -> str:
    """Strip tags and undo the HTML escaping, for assertions."""
    return html.unescape(re.sub(r"<[^>]+>", " ", page_html))


def test_getting_started_comes_first():
    assert PAGES[0].key == GETTING_STARTED_KEY


def test_every_action_and_category_has_a_page():
    keys = [page.key for page in PAGES]
    assert len(keys) == len(set(keys))
    for category in REGISTRY.by_category():
        assert category_key(category) in keys
    for action in REGISTRY:
        assert action.key in keys


def test_pages_are_grouped_under_their_category():
    for category, actions in REGISTRY.by_category().items():
        keys = [page.key for page in PAGES]
        first = keys.index(category_key(category)) + 1
        last = first + len(actions)
        assert keys[first:last] == [action.key for action in actions]


def test_every_category_has_an_introduction():
    assert set(REGISTRY.by_category()) <= set(CATEGORY_INTROS)


def test_getting_started_shows_real_steps_and_script():
    text = _text(PAGES[0].html)
    for key, _ in GETTING_STARTED_STEPS:
        assert REGISTRY.get(key).label in text
    assert "df.groupby(['city'], as_index=False)[['score']]" in text
    assert "ax.bar(df['city'], df['score'], color='tab:green')" in text
    assert "pd.read_csv('amazeplot-example.csv')" in text
    assert "plt.show()" in text
    # The table after the groupby step: one row per known city.
    assert "Lima" in text and "7.375" in text


@pytest.mark.parametrize("action", list(REGISTRY), ids=lambda a: a.key)
def test_action_page_documents_everything(action):
    page = action_page(action)
    text = _text(page.html)
    assert page.category == action.category
    assert action.label in text
    for param in action.parameters:
        assert param.label in text
    resolved = action.resolve_params(action.example, EXAMPLE_COLUMNS)
    assert action.to_code(resolved) in text
    assert action.documentation_url in page.html


def test_options_table_explains_kinds_and_defaults():
    text = _text(action_page(REGISTRY.get("dropna")).html)
    assert "One of: any, all." in text
    assert "One or more columns" in text
    assert "automatic" in text


def test_page_without_options():
    text = _text(action_page(REGISTRY.get("transpose")).html)
    assert "This tool has no options." in text
    assert "the default settings" in text


def test_text_is_escaped():
    page = action_page(REGISTRY.get("query"))
    assert "city == 'Rome'" not in page.html
    assert "&#x27;Rome&#x27;" in page.html
