# CLAUDE.md — rules for working on amazeplot

amazeplot is a PySide6 desktop GUI that exposes pandas DataFrame methods
as forms and exports every session as a runnable pandas script. Read
`docs/PLAN.md` (roadmap) and `docs/architecture.md` (design) before
making structural changes.

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
   - `amazeplot.operations` contains declarations only, with no widgets.
   - `amazeplot.gui` contains no pandas logic beyond displaying data. It
     calls the session and operations.
2. **The `DataSession` is the single source of truth.** Views never keep
   their own copy of the state. They subscribe and redraw in `refresh()`.
3. **Operations are declarative.** Each one is described by `Parameter`
   metadata, and the GUI builds its forms from that metadata. Never
   write a dialog by hand for a single operation.
4. **Execution and code generation share one source.** For
   `MethodOperation`, both come from `build_kwargs`. Custom `Operation`
   subclasses must keep `_execute` and `to_code` exactly equivalent.
5. **Never mutate the input DataFrame.** Operations return a new frame,
   and `inplace=True` is forbidden.
6. **No global mutable state.** Pass `OperationRegistry` and
   `DataSession` in explicitly (dependency injection). There are no
   module-level singletons.
7. **Never load pickles** or other formats that execute code when read.

## Adding operations

Follow `docs/adding_operations.md`. In short:

- `Parameter.name` is the pandas keyword name, and `Parameter.default`
  equals the pandas default. Values equal to the default are omitted
  from calls and generated code.
- Register the operation in its module's `OPERATIONS` tuple.
- Add an example to `EXAMPLES` in `tests/core/test_builtin_operations.py`
  (the contract test fails without one).

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

- User-caused failures raise subclasses of `AmazeplotError`
  (`OperationError`, `ParameterError`, `DataIOError`, `SessionError`),
  with messages written for end users.
- Use `raise ... from exc` when wrapping, to keep the cause.
- Broad `except Exception` is allowed **only** at a documented boundary
  (currently `Operation.execute`). Anywhere else, catch specific
  exceptions.
- The GUI catches `AmazeplotError` and shows it. Anything else is a bug
  and reaches the global exception hook in `gui/app.py`.

## Testing

- Every change to `core/` or `operations/` needs unit tests in
  `tests/core/`, which run without Qt.
- GUI changes need a pytest-qt test in `tests/gui/` (use the `qtbot`
  fixture). Keep logic out of widgets so that most behaviour can be
  tested in the core.
- Give widgets small public accessors for tests (`values()`,
  `preview_text()`, `status_text()`) rather than poking at private Qt
  children. Never open modal dialogs (`exec()`, `QMessageBox`) in tests.
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
