# CLAUDE.md — rules for working on amazeplot

amazeplot is a PySide6 desktop GUI that exposes pandas DataFrame methods
and matplotlib plotting functions as forms, and exports every session as
a runnable pandas/matplotlib script. Read `docs/PLAN.md` (roadmap) and
`docs/architecture.md` (design) before making structural changes.

Vocabulary: an **action** is anything in the toolbox. A **data
operation** (`Operation`) turns the DataFrame into a new one; a **plot
call** (`PlotCall`, usually an `AxesCall`) draws a **layer** on the
figure.

## Commands

```bash
pip install -e ".[dev]"        # install with dev tools
python -m amazeplot [file]     # run the app (optionally opening a file)
ruff format .                  # format (PEP 8, 79 columns)
ruff check .                   # lint: pycodestyle, pyflakes, naming, docstrings
python -m pytest               # all tests; GUI tests run offscreen
```

Before you commit, all three of `ruff format --check .`, `ruff check .`
and `python -m pytest` must pass.

## Architecture rules

1. **Layering is strict:** `gui → operations → core`.
   - `amazeplot.core` must never import Qt/PySide6 or `amazeplot.gui`.
   - `amazeplot.operations` is the catalogue of actions. It contains
     declarations only, with no widgets.
   - `amazeplot.gui` contains no pandas or plotting logic beyond
     displaying results. It calls the session and the actions.
   - Never import `matplotlib.pyplot` in the package: it holds global
     state. Use `matplotlib.figure.Figure`/`Axes` in the core and
     `backend_qtagg` in the GUI. Only *generated scripts* use pyplot.
2. **Never hand a whole DataFrame to Qt.** The Data tab shows one
   `RowWindow` slice (`gui/row_window.py`, `gui/data_view.py`), and
   expensive views (the figure) are only redrawn while visible. Measure
   with a table of a few million rows before adding a view that touches
   every row.
3. **The `DataSession` is the single source of truth.** That includes
   the plot layers. Views never keep their own copy of the state. They
   subscribe and redraw in `refresh()`. Every change pushes an immutable
   snapshot, so undo/redo must keep working for any new kind of state.
4. **Actions are declarative.** Each one is described by `Parameter`
   metadata, and the GUI builds its forms from that metadata. Never
   write a dialog by hand for a single action.
5. **Execution and code generation share one source.** For
   `MethodOperation` both come from `build_kwargs`, and for `AxesCall`
   both come from `build_arguments` (with `ColumnRef` placeholders).
   Custom subclasses must keep `_execute`/`_draw` and `to_code` exactly
   equivalent.
6. **Never mutate the input DataFrame.** Operations return a new frame,
   plot calls only read it, and `inplace=True` is forbidden.
7. **No global mutable state.** Pass `OperationRegistry` and
   `DataSession` in explicitly (dependency injection). There are no
   module-level singletons.
8. **Formats that execute code when read need explicit consent.**
   Pickles (`.pkl`, `.pickle`) are listed in `UNSAFE_EXTENSIONS` in
   `core/io.py`. Code that loads a user-chosen file must check
   `executes_code_on_read(path)` and ask the user first, with "No" as
   the default (see `MainWindow.open_file`). Never write pickles, and
   never store pickled data in project or session files.

## Adding operations and plots

Follow `docs/adding_operations.md`. In short:

- `Parameter.name` is the pandas/matplotlib keyword name, and
  `Parameter.default` equals the library default (`None` means "let the
  library decide"). Values equal to the default are omitted from calls
  and generated code.
- Register the action in its module's `ACTIONS` tuple.
- Give every action an `example=` that works on the example data
  (`core/examples.py`: columns `name`, `city`, `age`, `score`). The
  help pages show it and the contract tests run it; the suite fails
  without one.
- **Help is generated, never hand-written per tool.** Each tool's help
  page comes from its label, description, parameter labels and `help`
  texts, example and documentation link (`gui/help_pages.py`). Write
  those for end users. Only the worked example on the first page
  (`GETTING_STARTED_STEPS`) and the category introductions
  (`CATEGORY_INTROS`) are written by hand, and they run as tests.

## Coding style

- Follow **PEP 8**: 4-space indentation, lines of at most **79
  characters**, `snake_case` for functions and variables, `PascalCase`
  for classes, `UPPER_CASE` for constants, and a leading `_` for private
  names. `ruff format` is the formatter and is authoritative.
  - Exception: Qt virtual overrides keep their camelCase names
    (`rowCount`, `headerData`, ...). They're listed under
    `extend-ignore-names` in `pyproject.toml`.
- Imports: standard library, then third-party, then first-party, each
  group sorted (ruff `I`). Use absolute imports (`from amazeplot.core
  ...`). Never use `import *`.
- Start every module with `from __future__ import annotations` when it
  uses forward references or modern type syntax.
- **Type hints** on every public function, method and attribute.
- **Docstrings** (PEP 257, numpy convention) on every public module,
  class, function and method. Document `Parameters`, `Returns` and
  `Raises` when they aren't obvious. Comments explain *why*, not *what*.
- Prefer frozen `@dataclass`es for value objects and small,
  single-purpose functions (aim for under about 40 lines).
- Use dispatch tables (`dict[Kind, Handler]`) rather than long
  `if/elif` chains on enums, as in `_VALIDATORS` and `EDITOR_CLASSES`.
- No magic numbers or strings in logic. Name them as module constants.
- Don't use `print`. Use `logging.getLogger(__name__)`.

## Error handling

- User-caused failures raise subclasses of `AmazeplotError`, with
  messages written for end users. Action failures are `ActionError`s:
  `ParameterError`, `OperationError` (pandas) or `PlotError`
  (matplotlib). The others are `DataIOError` and `SessionError`.
- Use `raise ... from exc` when wrapping, to keep the cause.
- Broad `except Exception` is allowed **only** at a documented boundary
  (currently `Operation.execute` and `PlotCall.draw`). Anywhere else,
  catch specific exceptions.
- The GUI catches `AmazeplotError` and shows it. Anything else is a bug
  and reaches the global exception hook in `gui/app.py`.

## Testing

- Every change to `core/` or `operations/` needs unit tests in
  `tests/core/`, which run without Qt.
- GUI changes need a pytest-qt test in `tests/gui/` (use the `qtbot`
  fixture). Keep logic out of widgets so that most behaviour can be
  tested in the core.
- Give widgets small public accessors for tests (`values()`,
  `set_values()`, `confirm()`, `preview_text()`, `status_text()`) rather
  than poking at private Qt children. Every `ParameterEditor` implements
  `value()` and `set_value()`. Never open modal dialogs (`exec()`,
  `QMessageBox`) in tests.
- Tests run with `QT_QPA_PLATFORM=offscreen` and `MPLBACKEND=Agg` (set
  in `tests/conftest.py`). Inspect figures through `Axes` objects, not
  rendered images.
- Use the shared `people` fixture from `tests/conftest.py` for sample
  data.

## Documentation

- Update `README.md` for user-visible changes, `docs/architecture.md`
  for structural changes, and tick items off in `docs/PLAN.md` when a
  milestone task is completed.
- Keep docstrings in sync with behaviour. An outdated docstring is a bug.

## Git

- Small, focused commits with imperative subject lines (≤ 72 chars),
  e.g. `Add round operation`.
- Don't commit generated files, virtualenvs or data files (see
  `.gitignore`).
