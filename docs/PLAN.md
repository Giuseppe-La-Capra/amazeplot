# amazeplot — Project Plan

## 1. Vision

amazeplot is a desktop application that lets people explore, clean and
summarise tabular data with **pandas**, without writing code, while
showing them **the exact pandas code** behind every click.

Every session can be exported as a runnable Python script, so the GUI is
also a teaching tool and an on-ramp to scripting. The results are always
reproducible.

### Goals

1. Expose the most useful `pandas.DataFrame` methods through forms that
   are generated automatically from declarative metadata.
2. Make every action reversible (undo/redo) and reproducible (code
   export).
3. Keep the data logic completely independent of the GUI, so it can be
   tested headlessly and reused (CLI, notebook, web front-end).
4. Make adding a new pandas method a matter of minutes: one declaration
   plus one test example.

### Non-goals (for now)

- Editing individual cells by hand (it can't be reproduced as code).
- Being a spreadsheet replacement or a BI/dashboard tool.
- Handling data that does not fit in memory (see the risks section).

## 2. Target users and user stories

| As a…                 | I want to…                                       | So that…                               |
|-----------------------|--------------------------------------------------|----------------------------------------|
| Analyst without Python | open a CSV, drop empty rows and group by a column | I get a summary without writing code    |
| Python learner        | see the pandas code generated for my clicks      | I learn the API by example              |
| Data scientist        | prototype a cleaning pipeline visually           | I can paste the exported script into my project |
| Anyone                | undo a mistaken step                             | I can experiment safely                 |

## 3. Technology choices

| Concern        | Choice                     | Rationale |
|----------------|----------------------------|-----------|
| Language       | Python ≥ 3.10              | Same language as pandas; modern typing syntax. |
| GUI toolkit    | **PySide6 (Qt 6)**         | Official Qt binding with an LGPL licence; `QAbstractTableModel` displays large frames lazily; mature docking, dialogs and testing (`pytest-qt`). Tkinter lacks a performant table widget; web frameworks (Streamlit, Dash) don't give a desktop app with offline file access and native dialogs. |
| Data           | pandas ≥ 2.1               | Copy-on-write makes cheap history snapshots possible. |
| Tests          | pytest + pytest-qt         | Standard; GUI tests run headless with `QT_QPA_PLATFORM=offscreen`. |
| Lint / format  | ruff (79 columns, PEP 8, PEP 257, numpy docstrings) | One fast tool for pycodestyle, pyflakes, isort, naming and docstrings. |
| Packaging      | `pyproject.toml`, setuptools, `src/` layout | The src layout stops tests from accidentally importing the working tree. |

## 4. Architecture (summary)

```
┌──────────────────────── amazeplot.gui (PySide6) ───────────────────────┐
│ MainWindow ─ OperationsPanel ─ OperationDialog ─ ParameterEditors      │
│      │                                   ▲                             │
│      │ subscribe / apply / undo          │ reads Operation.parameters  │
└──────┼───────────────────────────────────┼─────────────────────────────┘
       ▼                                   │
┌──────────────────────── amazeplot.core (no Qt) ────────────────────────┐
│ DataSession ── Step ── Operation ── Parameter    io    codegen          │
└──────────────────────────────────▲─────────────────────────────────────┘
                                   │ registered in
┌──────────────────────── amazeplot.operations ──────────────────────────┐
│ select · clean · transform · aggregate   (declarative catalogue)       │
└────────────────────────────────────────────────────────────────────────┘
```

Dependencies only point **downwards**: `gui → operations → core`. See
[architecture.md](architecture.md) for the details.

## 5. Milestones

### M1 — Foundations (done in this iteration)

- [x] Project skeleton: `pyproject.toml`, src layout, ruff, pytest, CI.
- [x] Core model: `Parameter`, `Operation`, `MethodOperation`,
      `OperationRegistry`, `DataSession` (undo/redo, observers).
- [x] File I/O: CSV, TSV, JSON, Excel\*, Parquet\* (\* optional extras).
- [x] Code generation: export the session as a runnable script.
- [x] 22 built-in operations in four categories (Select, Clean,
      Transform, Aggregate).
- [x] GUI: main window, lazy table model, searchable operations tree,
      auto-generated parameter dialog with live code preview and inline
      errors, history panel with the generated code.
- [x] Contract test: for every operation, the generated code reproduces
      the GUI result exactly.

### M2 — Usability

- [ ] Preview of the result (first 50 rows) inside the operation dialog.
- [ ] Column context menu in the table header (sort, rename, drop,
      change type, fill missing) that reuses the same operations.
- [ ] Column statistics side panel (dtype, missing count, unique count,
      min/max, histogram).
- [ ] "Recent files" menu and remembered window layout (`QSettings`).
- [ ] Clicking a history step jumps to that point (truncating redo).
- [ ] Options in the Open dialog for the reader (separator, encoding,
      header row, sheet name).

### M3 — Plotting (the "plot" in amazeplot)

- [ ] `PlotSpec` model in the core (kind, x, y, hue, aggregation),
      generated from the same `Parameter` metadata.
- [ ] Matplotlib canvas (`FigureCanvasQTAgg`) in a dockable panel.
- [ ] Plot kinds: line, bar, scatter, histogram, box, heatmap (for
      `corr`).
- [ ] Plots are included in the exported script (`df.plot(...)`).
- [ ] Export figure to PNG/SVG.

### M4 — Multiple datasets

- [ ] Sessions hold several named frames (tabs).
- [ ] `merge`, `concat` and `join` operations, using a new
      `ParameterKind.DATASET`.
- [ ] Code export with one variable per dataset.

### M5 — Scale and robustness

- [ ] Run operations in a worker thread (`QThreadPool`) with a busy
      indicator and cancellation, so the UI never freezes.
- [ ] A memory budget for the history: drop the oldest snapshots and
      recompute them from the script on demand.
- [ ] Save and reopen a session (`.amazeplot` JSON file storing the
      source and steps, never pickled data).

### M6 — Distribution

- [ ] Stand-alone builds with PyInstaller for Windows, macOS and Linux.
- [ ] User guide with screenshots (MkDocs) and an API reference.
- [ ] Plugin entry point (`amazeplot.operations` entry-point group) so
      third parties can ship their own operations.

## 6. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Large files freeze the UI | Lazy table model (M1); background execution (M5). |
| Many history snapshots exhaust memory | Copy-on-write sharing (M1); history budget (M5). |
| Generated code drifts from GUI behaviour | Execution and code come from the same kwargs; contract test over every operation. |
| `query` expressions are evaluated | They only run on the user's own data on their own machine; we never load pickles, and session files will store no executable content. |
| pandas API changes | Pin a minimum version; CI runs the contract tests against the latest pandas. |

## 7. Definition of done (for every feature)

1. The code follows the rules in [`CLAUDE.md`](../CLAUDE.md) (PEP 8,
   typed, documented).
2. `ruff check .`, `ruff format --check .` and `python -m pytest` all pass.
3. Core logic has unit tests; GUI behaviour has at least one pytest-qt
   test.
4. User-visible behaviour is documented (README or `docs/`).
