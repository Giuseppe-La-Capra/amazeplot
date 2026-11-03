# Adding a new operation or plot

Most pandas methods and matplotlib `Axes` methods can be exposed in
three steps without touching the GUI. Both are *actions*: they are
declared in a module of `src/amazeplot/operations/` and listed in that
module's `ACTIONS` tuple.

# Data operations (pandas)

## 1. Declare the operation

Pick the module that matches the GUI category (`select.py`, `clean.py`,
`transform.py`, `aggregate.py`), or create a new module for a new
category (with its own `ACTIONS` tuple) and add it to `_MODULES` in
`operations/__init__.py`.

```python
# src/amazeplot/operations/transform.py
ROUND = MethodOperation(
    key="round",                      # unique, snake_case
    label="Round numbers",            # shown in the tree and dialog title
    category=CATEGORY,
    description="Round numeric columns to a number of decimals.",
    parameters=(
        Parameter(
            name="decimals",          # == the pandas keyword argument
            label="Decimals",
            kind=ParameterKind.INTEGER,
            default=0,                # == the pandas default
            minimum=0,
        ),
    ),
    method="round",                   # DataFrame method to call
)

ACTIONS = (..., ROUND)               # register it in the module tuple
```

Rules:

- `Parameter.name` **must** be the pandas keyword name, and
  `Parameter.default` **must** equal the pandas default. Values equal to
  the default are left out of the call and the generated code, so a
  wrong default silently changes behaviour.
- Use `kwargs_builder` when the widgets don't map one-to-one onto
  keyword arguments (see `RENAME_COLUMN` or `FILLNA`).
- Use `then="reset_index"` when the method returns a Series or puts keys
  in the index and you want a flat table back.
- If the expression needs several chained calls, subclass `Operation`
  and implement `_execute` and `to_code` (see `GroupByOperation`).
- Operations must **return a new DataFrame** and never use
  `inplace=True`.

## 2. Add a contract-test example

Add an entry to `EXAMPLES` in `tests/core/test_builtin_operations.py`:

```python
"round": {"decimals": 1},
```

The suite now checks that the operation runs on the shared `people`
fixture, that it doesn't mutate its input, and that its generated code
reproduces the result exactly. If the operation has its own logic (a
`kwargs_builder` or a custom class), add focused unit tests too.

## 3. Check

```bash
ruff format .
ruff check .
python -m pytest
```

# Plot calls (matplotlib)

## 1. Declare the plot call

Plot calls live in `plot.py` (they draw data) and `decorate.py` (they
change the axes: titles, scales, guides). Most are an `AxesCall`, which
calls one `matplotlib.axes.Axes` method:

```python
# src/amazeplot/operations/plot.py
VIOLIN = AxesCall(
    key="plot_violin",                # unique, snake_case
    label="Violin plot",
    category=CATEGORY,
    description="Distribution shape of one or more numeric columns.",
    parameters=(
        _columns("dataset", "Columns"),   # COLUMNS -> [df['a'], ...]
        Parameter(
            "showmeans", "Show means", ParameterKind.BOOLEAN,
            default=False,            # == the matplotlib default
        ),
        ORIENTATION,                  # shared styling parameter
    ),
    method="violinplot",              # Axes method to call
    positional=("dataset",),          # passed positionally, in order
    dropna=True,                      # violinplot fails on NaN
)

ACTIONS = (..., VIOLIN)
```

Rules, in addition to those for data operations:

- `COLUMN` parameters are passed as `df['column']` and `COLUMNS`
  parameters as a list of them. Other kinds are passed as plain values.
- List the parameters that matplotlib takes positionally (usually the
  data, such as `x` and `y`) in `positional`. Empty positional values
  are skipped, which is how `ax.plot(y)` works without `x`.
- Optional styling parameters use `default=None` ("let matplotlib
  decide"). The editors show "(default)" and the value is omitted. Reuse
  the shared ones in `_common.py` (`COLOR`, `ALPHA`, `LINESTYLE`,
  `MARKER`, `COLORMAP`, ...).
- Use `extra_kwargs` for arguments computed from other parameters (for
  example, legend labels from column names), `numeric_frame=True` to
  pass all numeric columns (`imshow`), and `dropna=True` when matplotlib
  rejects missing values.
- If the drawing needs several calls, subclass `PlotCall` and implement
  `_draw` and `to_code`, keeping them exactly equivalent.
- Never use `matplotlib.pyplot` outside generated code.

## 2. Add a contract-test example

Add an entry to `EXAMPLES` in `tests/core/test_builtin_plots.py`, using
columns of the shared `people` fixture:

```python
"plot_violin": {"dataset": ["age", "score"]},
```

The suite now checks three things: the example changes the axes, the
generated code draws the same artists as the GUI, and the DataFrame is
not mutated.

## 3. Check

Run the same three commands as above.

## Adding a new parameter kind

You only need this when no existing `ParameterKind` fits (for example, a
date or a second dataset).

1. Add a member to `ParameterKind` in `core/parameters.py`, plus a
   validator in `_VALIDATORS`.
2. Add a `ParameterEditor` subclass in `gui/parameter_editors.py` and
   register it in `EDITOR_CLASSES`.
3. `test_every_kind_has_an_editor` fails until step 2 is done. Add an
   editor default test to `tests/gui/test_parameter_editors.py`.
