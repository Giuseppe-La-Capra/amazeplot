# Architecture

This document explains how amazeplot is put together, so you can find
the right place for a change.

Everything the user can pick from the toolbox is an **action**. There
are two kinds: **data operations** turn the DataFrame into a new one
(pandas), and **plot calls** draw a layer on the figure (matplotlib).

## Layers

```
src/amazeplot/
├── core/            # Model layer. pandas + matplotlib (object API only).
│   │                  # NO Qt imports, NO matplotlib.pyplot.
│   ├── errors.py      exception hierarchy (AmazeplotError and children)
│   ├── parameters.py  Parameter / ParameterKind: declarative inputs
│   ├── action.py      Action: metadata, parameter resolution, to_code
│   ├── operation.py   Operation (an Action), MethodOperation
│   ├── plotting.py    PlotCall (an Action), AxesCall, Layer, ColumnRef
│   ├── registry.py    ActionRegistry: the catalogue
│   ├── session.py     DataSession, Step: state, history, undo/redo
│   ├── io.py          DataSource, load_dataframe, save_dataframe
│   └── codegen.py     generate_script: session -> runnable Python
├── operations/      # The catalogue of built-in actions (data only).
│   ├── select.py, clean.py, transform.py, aggregate.py  (pandas)
│   ├── plot.py, decorate.py                             (matplotlib)
│   └── __init__.py    build_default_registry()
└── gui/             # View/controller layer. PySide6.
    ├── app.py               main(): wiring + exception hook
    ├── main_window.py       MainWindow: controller, tabs, menus, docks
    ├── dataframe_model.py   DataFrameModel: QAbstractTableModel
    ├── plot_panel.py        matplotlib canvas, toolbar, layer list
    ├── actions_panel.py     searchable tree of actions (the toolbox)
    ├── action_dialog.py     form generated from Action.parameters
    ├── parameter_editors.py one editor widget per ParameterKind
    └── history_panel.py     applied steps + generated script
```

**Dependency rule:** `gui` may import `operations` and `core`;
`operations` may import `core`; `core` imports neither. This lets the
whole data layer be tested without a display, and reused by other
front-ends. The core uses matplotlib's object-oriented API
(`matplotlib.figure.Figure`, `Axes`) but never `matplotlib.pyplot`,
which keeps a global "current figure". Only exported scripts use pyplot.

## Key abstractions

### `Parameter`

A frozen dataclass that describes one input: its name (which is the
pandas keyword name), label, `ParameterKind`, default, whether it is
required, its choices and bounds. Parameters know how to `coerce` raw
editor values (for example, parsing `"0"` into `0` for `VALUE`) and how
to `validate` them against the current columns.

### `Action`

An abstract frozen dataclass holding the metadata (`key`, `label`,
`category`, `description`, `parameters`). It has two responsibilities
shared by every toolbox entry:

- `resolve_params(params, columns)` fills in defaults, coerces and
  validates values. It raises `ParameterError`.
- `to_code(params, variable)` returns a single Python statement.

The dialog, the toolbox tree and the code preview only know about
`Action`, so they work unchanged for data operations and plot calls.

### `Operation`

An `Action` that transforms data. `apply(frame, params)` resolves the
parameters and then calls `execute`, which runs `_execute` and turns any
pandas exception into `OperationError`.

`MethodOperation` covers the common case `df = df.<method>(**kwargs)`.
It derives **both** the call and the code from `build_kwargs`, so they
can't drift apart. An optional `kwargs_builder` handles methods whose
arguments don't map one-to-one onto widgets (`rename(columns={a: b})`),
and an optional `then` chains a no-argument method (`.reset_index()`).

When an expression needs several chained calls, subclass `Operation`
directly (see `GroupByOperation` in `operations/aggregate.py`).

### `PlotCall`, `AxesCall` and `Layer`

A `PlotCall` is an `Action` that draws on a matplotlib `Axes`.
`draw(frame, params, axes)` runs `_draw` and turns any failure into
`PlotError`. `check(frame, params)` draws once on a throw-away `Figure`,
so a failing layer is rejected before it reaches the session.

`AxesCall` covers the common case `ax.<method>(*args, **kwargs)`:

- Parameters listed in `positional` are passed positionally (empty ones
  are skipped). The rest become keyword arguments, omitted when empty or
  equal to the default, exactly like `MethodOperation`.
- `COLUMN` values become `ColumnRef` placeholders and `COLUMNS` values
  become lists of them. `build_arguments` returns arguments that still
  contain the placeholders. `resolve_argument` swaps them for the
  columns of the DataFrame (to draw), and `render_argument` turns them
  into `df['column']` source (to generate code). Drawing and code
  therefore come from one source.
- `numeric_frame=True` passes `df.select_dtypes('number')` (heatmaps),
  `dropna=True` appends `.dropna()` to every column (histograms and box
  plots fail on NaN), and `extra_kwargs` adds computed arguments such as
  legend labels taken from column names.

A `Layer` is a plot call plus its resolved parameters, like `Step` for
operations. The figure is the ordered list of layers drawn on one
`Axes` by `render_layers`.

### `DataSession`

This is the single source of truth. Its state is a stack of immutable
snapshots, each holding the current DataFrame, the data `Step`s and the
plot `Layer`s. `apply`, `add_layer`, `remove_layer` and `clear_layers`
each push a new snapshot. Undo/redo moves snapshots between two stacks,
so they never re-run pandas or matplotlib, and one history covers data
and plots. Plot layers survive data steps; if a layer no longer fits the
data (say its column was dropped), the Plot tab reports it.

Observers register with `subscribe()`; the GUI redraws on every
notification. The session stays Qt-free by using plain callbacks rather
than Qt signals.

### Code generation

`generate_script(session)` emits:

```python
"""Data pipeline generated by amazeplot."""

import pandas as pd

df = pd.read_csv('people.csv')
df = df.dropna(subset=['age'])
df = df.groupby(['city'], as_index=False)[['score']].agg('mean')
```

When the session has plot layers, the script also imports pyplot and
appends the figure:

```python
fig, ax = plt.subplots()
ax.bar(df['city'], df['score'], color='tab:green')
ax.set_title('Mean score per city')
plt.show()
```

## Data flow of one action

1. The user activates an entry in `ActionsPanel`, which emits
   `action_requested(action)`.
2. `MainWindow.request_action` opens an `ActionDialog`, which creates
   one `ParameterEditor` per `Parameter` via `create_editor`.
3. As the user types, the dialog calls `resolve_params` and `to_code` to
   show a live code preview, or the validation message.
4. On *OK*, the dialog calls the callback chosen by
   `MainWindow._apply_callback` from the action type:
   `session.apply(operation, values)` for an `Operation`, or
   `session.add_layer(call, values)` for a `PlotCall`. If that raises
   `ActionError`, the dialog shows the message and stays open.
5. On success, the session pushes a snapshot and notifies its
   listeners. `MainWindow.refresh` then updates the table model, the
   plot panel, the history panel, the action states and the status bar.
   The window switches to the Data or Plot tab to show the result.

## Error handling policy

| Kind of failure | Exception | Where it's handled |
|-----------------|-----------|--------------------|
| Invalid user input | `ParameterError` (an `ActionError`) | Dialog shows it inline. |
| pandas rejects the call | `OperationError` (an `ActionError`, wraps the original via `from`) | Dialog shows it inline. |
| matplotlib rejects the call | `PlotError` (an `ActionError`) | Dialog shows it inline; for existing layers, the Plot tab shows it. |
| Unreadable or unwritable file | `DataIOError` | Main window shows a warning. |
| Invalid session state | `SessionError` | The GUI prevents it by disabling actions. |
| A bug (anything else) | any | Global `sys.excepthook` logs the traceback and shows a dialog. |

Broad `except Exception` appears in **two** places only, both
documented: the `Operation.execute` and `PlotCall.draw` boundaries.

## Testing strategy

- `tests/core/` — fast, headless unit tests of the model layer.
- `tests/core/test_builtin_operations.py` — the **contract test** for
  data operations. For every registered operation it applies an
  example, executes the generated code, and asserts the two results are
  identical. It also checks that no operation mutates its input. A new
  operation without an example makes the suite fail.
- `tests/core/test_builtin_plots.py` — the same contract for plot calls.
  It draws each example with the GUI path and with the generated code on
  two fresh `Axes`, then compares a fingerprint of everything drawn
  (artists, data, texts, scales, limits, grid, legend). A guard test
  checks that each example really changes the axes, so the comparison
  can't pass vacuously.
- `tests/gui/` — pytest-qt tests of the model, editors, dialog, plot
  panel and main window, running with `QT_QPA_PLATFORM=offscreen` and
  `MPLBACKEND=Agg`.
