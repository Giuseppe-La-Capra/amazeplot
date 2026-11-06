"""Help pages generated from the action catalogue.

Nothing here is written by hand per tool. Every page is built from the
action metadata (label, description, parameters, example) and from
running the examples, so the help can never drift from the tools. The
module is Qt-free: it only produces HTML for :class:`HelpWindow`.
"""

from __future__ import annotations

import html
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from amazeplot.core.action import Action
from amazeplot.core.codegen import generate_script
from amazeplot.core.examples import (
    EXAMPLE_COLUMNS,
    EXAMPLE_FILE_NAME,
    example_data,
)
from amazeplot.core.io import DataSource
from amazeplot.core.operation import Operation
from amazeplot.core.parameters import Parameter, ParameterKind
from amazeplot.core.registry import ActionRegistry
from amazeplot.core.session import DataSession

GETTING_STARTED_KEY = "getting-started"
"""Key of the first help page: a worked example."""

GETTING_STARTED_STEPS: tuple[tuple[str, Mapping[str, Any]], ...] = (
    ("groupby", {"by": ["city"], "columns": ["score"], "func": "mean"}),
    ("plot_bar", {"x": "city", "height": "score", "color": "tab:green"}),
    ("set_title", {"label": "Mean score per city"}),
    ("set_ylabel", {"ylabel": "Score"}),
)
"""Toolbox actions (key, settings) of the worked example, in order."""

CATEGORY_INTROS: Mapping[str, str] = {
    "Select": "Keep only some of the rows or columns of the table.",
    "Clean": "Fix missing, duplicated, misnamed or wrongly typed values.",
    "Create": (
        "Add new columns computed from existing ones: a function of one "
        "column (for complex numbers: absolute value, phase, real and "
        "imaginary parts), or an expression combining several columns."
    ),
    "Transform": "Reorder or reshape the table.",
    "Aggregate": (
        "Summarise the table: groups, counts, statistics and pivots. "
        "The summary replaces the table; undo to get the rows back."
    ),
    "Plot": (
        "Draw the data. Each plot is a layer added to the figure in the "
        "Plot tab, and layers are drawn on top of each other, so you can "
        "combine several plots in one figure."
    ),
    "Decorate": (
        "Finish the figure: titles, axis labels, a legend, a grid, "
        "scales, ranges, reference lines and text. Decorations are "
        "layers too, so you can undo or remove them."
    ),
}
"""One-paragraph introduction of each toolbox category."""

_AUTOMATIC = "automatic"
_EXAMPLE_COLUMN_TEXT = ", ".join(EXAMPLE_COLUMNS)
_STYLE = """
<style>
  h1 { margin-bottom: 4px; }
  h2 { margin-top: 18px; }
  pre { margin-left: 12px; }
  .muted { color: gray; }
</style>
"""


@dataclass(frozen=True)
class HelpPage:
    """One page of the help window.

    Attributes
    ----------
    key : str
        Unique identifier: :data:`GETTING_STARTED_KEY`, a category key
        (see :func:`category_key`) or an action key.
    title : str
        Text shown in the table of contents.
    html : str
        Page content.
    category : str or None
        Category of an action page; ``None`` for top-level pages.
    """

    key: str
    title: str
    html: str
    category: str | None = None


def category_key(category: str) -> str:
    """Return the page key of a toolbox category."""
    return f"category:{category}"


def build_help_pages(registry: ActionRegistry) -> list[HelpPage]:
    """Return every help page, in table-of-contents order.

    The worked example comes first, then each category followed by the
    pages of its tools.

    Raises
    ------
    AmazeplotError
        If the worked example no longer runs (a bug, caught by tests).
    """
    pages = [getting_started_page(registry)]
    for category, actions in registry.by_category().items():
        pages.append(category_page(category, actions))
        pages += [action_page(action) for action in actions]
    return pages


# -- Getting started -----------------------------------------------------


def getting_started_page(registry: ActionRegistry) -> HelpPage:
    """Return the first page: the window layout and a worked example.

    The example is actually run on the example data, so the steps, the
    resulting table and the exported script shown are always correct.
    """
    session = DataSession()
    session.load(
        example_data(), DataSource(Path(EXAMPLE_FILE_NAME), "read_csv")
    )
    steps = []
    for key, params in GETTING_STARTED_STEPS:
        action = registry.get(key)
        # Resolve before performing: the step itself changes the columns.
        columns = [] if session.frame is None else session.frame.columns
        code = action.to_code(action.resolve_params(params, list(columns)))
        session.perform(action, params)
        steps.append(_example_step(action, params, code, session))
    body = (
        "<h1>Getting started</h1>"
        "<p>amazeplot lets you transform a table with <b>pandas</b> and "
        "plot it with <b>matplotlib</b> without writing code. Every tool "
        "shows the Python code it runs, and you can export everything "
        "you did as a script.</p>"
        "<h2>The window</h2><ul>"
        "<li><b>Toolbox</b> (left): every tool, grouped by category. "
        "Type in the search box to find one, and double-click it to "
        "open its form. Each form has a <b>Help</b> button.</li>"
        "<li><b>Data</b> and <b>Plot</b> tabs (centre): the current "
        "table, and the figure built from your plot layers. Large tables "
        "are shown one page at a time: use the bar above the table to "
        "pick the first row (<b>Rows from</b>), the <b>Rows per "
        "page</b>, or <b>Previous</b>/<b>Next</b>. Every tool still "
        "works on the whole table. Click a cell to see the type and "
        "statistics of its column and all values of its row in the "
        "<b>info panel</b> under the table.</li>"
        "<li><b>History</b> (right): the steps you applied and the "
        "equivalent Python code.</li></ul>"
        "<h2>Example: mean score per city</h2>"
        "<p>This example uses the built-in example data: a table of 12 "
        f"people with the columns <i>{_EXAMPLE_COLUMN_TEXT}</i>.</p><ol>"
        "<li>Choose <b>Help &rarr; Open example data</b>. The table "
        "appears in the Data tab. (With your own data, use <b>File "
        "&rarr; Open</b>.)</li>"
        + "".join(steps)
        + "<li>Made a mistake? <b>Edit &rarr; Undo</b> (Ctrl+Z) reverts "
        "the last step, whether it changed the data or the plot.</li>"
        "<li><b>File &rarr; Export Python script</b> saves the whole "
        "session as a script that redoes it without amazeplot:"
        f"{_code(generate_script(session))}</li></ol>"
        "<h2>Next</h2><p>Pick any tool in the contents on the left to "
        "see what it does, its options and an example.</p>"
    )
    return HelpPage(GETTING_STARTED_KEY, "Getting started", _page(body))


def _example_step(
    action: Action,
    params: Mapping[str, Any],
    code: str,
    session: DataSession,
) -> str:
    """Describe one worked-example step, after it has been performed."""
    text = (
        f"<li>In the toolbox, open <b>{_esc(action.category)} &rarr; "
        f"{_esc(action.label)}</b>. Set "
        f"{_settings_sentence(action, params)}, then press <b>OK</b>. "
        f"This runs:{_code(code)}"
    )
    if isinstance(action, Operation):
        frame = session.frame
        text += "The Data tab now shows:" + (
            frame.to_html(index=False, border=1, na_rep="NaN")
            if frame is not None
            else ""
        )
    else:
        text += "The Plot tab shows the figure with this layer added."
    return text + "</li>"


# -- Category and action pages -------------------------------------------


def category_page(category: str, actions: Sequence[Action]) -> HelpPage:
    """Return the overview page of a toolbox category."""
    items = "".join(
        f"<li><b>{_esc(action.label)}</b>: {_esc(action.description)}</li>"
        for action in actions
    )
    body = (
        f"<h1>{_esc(category)}</h1>"
        f"<p>{_esc(CATEGORY_INTROS.get(category, ''))}</p>"
        f"<ul>{items}</ul>"
    )
    return HelpPage(category_key(category), category, _page(body))


def action_page(action: Action) -> HelpPage:
    """Return the help page of one tool."""
    body = (
        f"<h1>{_esc(action.label)}</h1>"
        f"<p class='muted'>Toolbox category: {_esc(action.category)}</p>"
        f"<p>{_esc(action.description)}</p>"
        f"<h2>Options</h2>{_options_table(action)}"
        f"{_example_section(action)}"
        f"{_reference_section(action)}"
    )
    return HelpPage(action.key, action.label, _page(body), action.category)


def _options_table(action: Action) -> str:
    if not action.parameters:
        return "<p>This tool has no options.</p>"
    rows = "".join(
        "<tr>"
        f"<td><b>{_esc(param.label)}</b></td>"
        f"<td>{_esc(_what_to_enter(param))}</td>"
        f"<td>{_esc(_default_text(param))}</td>"
        "</tr>"
        for param in action.parameters
    )
    return (
        "<table border='1' cellpadding='4' cellspacing='0'>"
        "<tr><th>Option</th><th>What to enter</th><th>Default</th></tr>"
        f"{rows}</table>"
        "<p class='muted'>&ldquo;Automatic&rdquo; means pandas or "
        "matplotlib chooses; the option is then left out of the "
        "code.</p>"
    )


def _example_section(action: Action) -> str:
    if action.example is None:
        return ""
    resolved = action.resolve_params(action.example, EXAMPLE_COLUMNS)
    settings = (
        f"with these settings: {_settings_sentence(action, action.example)}"
        if action.example
        else "with the default settings"
    )
    return (
        "<h2>Example</h2>"
        "<p>On the example data (<b>Help &rarr; Open example data</b>; "
        f"columns <i>{_EXAMPLE_COLUMN_TEXT}</i>), {settings}, the tool "
        f"runs:</p>{_code(action.to_code(resolved))}"
    )


def _reference_section(action: Action) -> str:
    url = action.documentation_url
    if url is None:
        return ""
    name = url.rsplit("/", 1)[-1].removesuffix(".html")
    return (
        "<h2>Learn more</h2><p>This tool calls "
        f"<a href='{_esc(url)}'>{_esc(name)}</a>. Its documentation "
        "describes every detail and option.</p>"
    )


# -- Formatting helpers --------------------------------------------------


def _range_text(param: Parameter) -> str:
    low, high = param.minimum, param.maximum
    if low is not None and high is not None:
        return f" between {_number(low)} and {_number(high)}"
    if low is not None:
        return f" of at least {_number(low)}"
    if high is not None:
        return f" of at most {_number(high)}"
    return ""


def _choices_text(param: Parameter) -> str:
    return ", ".join(_value_text(param, choice) for choice in param.choices)


_KIND_TEXT: Mapping[ParameterKind, Callable[[Parameter], str]] = {
    ParameterKind.COLUMN: lambda param: "One column.",
    ParameterKind.COLUMNS: lambda param: "One or more columns (tick them).",
    ParameterKind.CHOICE: lambda param: f"One of: {_choices_text(param)}.",
    ParameterKind.INTEGER: lambda param: (
        f"A whole number{_range_text(param)}."
    ),
    ParameterKind.FLOAT: lambda param: f"A number{_range_text(param)}.",
    ParameterKind.BOOLEAN: lambda param: "Tick or untick.",
    ParameterKind.TEXT: lambda param: "Text.",
    ParameterKind.VALUE: lambda param: (
        "A Python value: 0, 1.5, 'text', True or None."
    ),
}
"""How to fill in each kind of parameter, for the options table."""


def _what_to_enter(param: Parameter) -> str:
    text = _KIND_TEXT[param.kind](param)
    return f"{text} {param.help}" if param.help else text


def _default_text(param: Parameter) -> str:
    if param.required:
        return "required"
    return _value_text(param, param.default)


def _value_text(param: Parameter, value: Any) -> str:
    """Return ``value`` as a user would see or enter it in the form."""
    if value is None:
        return _AUTOMATIC
    if param.kind is ParameterKind.BOOLEAN:
        return "ticked" if value else "not ticked"
    if isinstance(value, (list, tuple)):
        return ", ".join(str(item) for item in value)
    if isinstance(value, float):
        return _number(value)
    return str(value)


def _settings_sentence(action: Action, params: Mapping[str, Any]) -> str:
    """Return "*Label*: value; ..." for the given settings, in form order."""
    parts = [
        f"<i>{_esc(param.label)}</i>: "
        f"{_esc(_value_text(param, params[param.name]))}"
        for param in action.parameters
        if param.name in params
    ]
    return "; ".join(parts) if parts else "nothing"


def _number(value: float) -> str:
    return f"{value:g}"


def _code(source: str) -> str:
    return f"<pre>{_esc(source.rstrip())}</pre>"


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _page(body: str) -> str:
    return f"<html><head>{_STYLE}</head><body>{body}</body></html>"
