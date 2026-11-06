# amazeplot — Project Plan

## 1. Vision

amazeplot is a desktop application that lets people explore, clean,
summarise and **plot** tabular data with **pandas** and **matplotlib**,
without writing code, while showing them **the exact code** behind every
click.

Every session can be exported as a runnable Python script, so the GUI is
also a teaching tool and an on-ramp to scripting. The results are always
reproducible.

### Goals

1. Expose the most useful `pandas.DataFrame` methods and matplotlib
   `Axes` plotting functions through forms that are generated
   automatically from declarative metadata.
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
| Analyst               | combine a scatter plot, a reference line and a legend | I can build exactly the chart I need |
| Data scientist        | prototype a cleaning pipeline visually           | I can paste the exported script into my project |
| Anyone                | undo a mistaken step                             | I can experiment safely                 |

## 3. Technology choices

| Concern        | Choice                     | Rationale |
|----------------|----------------------------|-----------|
| Language       | Python ≥ 3.10              | Same language as pandas; modern typing syntax. |
| GUI toolkit    | **PySide6 (Qt 6)**         | Official Qt binding with an LGPL licence; `QAbstractTableModel` displays large frames lazily; mature docking, dialogs and testing (`pytest-qt`). Tkinter lacks a performant table widget; web frameworks (Streamlit, Dash) don't give a desktop app with offline file access and native dialogs. |
| Data           | pandas ≥ 2.1               | Copy-on-write makes cheap history snapshots possible. |
| Plotting       | matplotlib ≥ 3.10 (object-oriented API, no pyplot in the app) | The reference Python plotting library; its `Axes` methods map one-to-one onto layers, and the Qt canvas embeds natively. pyplot is avoided in the app because it holds global state. |
| Tests          | pytest + pytest-qt         | Standard; GUI tests run headless with `QT_QPA_PLATFORM=offscreen`. |
| Lint / format  | ruff (79 columns, PEP 8, PEP 257, numpy docstrings) | One fast tool for pycodestyle, pyflakes, isort, naming and docstrings. |
| Packaging      | `pyproject.toml`, setuptools, `src/` layout | The src layout stops tests from accidentally importing the working tree. |

## 4. Architecture (summary)

```
┌──────────────────────── amazeplot.gui (PySide6) ───────────────────────┐
│ MainWindow ─ ActionsPanel ─ ActionDialog ─ ParameterEditors ─ PlotPanel│
│      │                                   ▲                             │
│      │ subscribe / apply / add_layer     │ reads Action.parameters     │
└──────┼───────────────────────────────────┼─────────────────────────────┘
       ▼                                   │
┌──────────────────── amazeplot.core (no Qt, no pyplot) ─────────────────┐
│ DataSession ── Step/Layer ── Action ─┬─ Operation    Parameter  codegen │
│                                      └─ PlotCall     io                 │
└──────────────────────────────────▲─────────────────────────────────────┘
                                   │ registered in
┌──────────────────────── amazeplot.operations ──────────────────────────┐
│ select · clean · transform · aggregate · plot · decorate (catalogue)   │
└────────────────────────────────────────────────────────────────────────┘
```

Dependencies only point **downwards**: `gui → operations → core`. See
[architecture.md](architecture.md) for the details.

## 5. Milestones

### M1 — Foundations (done)

- [x] Project skeleton: `pyproject.toml`, src layout, ruff, pytest, CI.
- [x] Core model: `Parameter`, `Operation`, `MethodOperation`,
      registry, `DataSession` (undo/redo, observers).
- [x] File I/O: CSV, TSV, JSON, Excel\*, Parquet\* (\* optional extras),
      and reading pickles after the user confirms.
- [x] Code generation: export the session as a runnable script.
- [x] 22 built-in operations in four categories (Select, Clean,
      Transform, Aggregate).
- [x] GUI: main window, lazy table model, searchable operations tree,
      auto-generated parameter dialog with live code preview and inline
      errors, history panel with the generated code.
- [x] Contract test: for every operation, the generated code reproduces
      the GUI result exactly.

### M2 — Usability

- [x] Help menu: a worked example first, then a generated page for every
      tool (options, example, documentation link); a Help button in
      every tool's dialog; built-in example data.
- [ ] Preview of the result (first 50 rows) inside the operation dialog.
- [ ] Column context menu in the table header (sort, rename, drop,
      change type, fill missing) that reuses the same operations.
- [x] Info panel under the table: dtype, counts, unique values, memory
      and statistics of the selected column; label and values of the
      selected row.
- [ ] Histogram of the selected column in the info panel.
- [x] Multi-level (MultiIndex) labels shown readably; Flatten column
      names operation.
- [x] Complex numbers: display, `complex128` column type, and automatic
      conversion of complex numbers stored as text in CSV files.
- [x] Create columns: a numpy function of a column (magnitude, phase,
      real/imaginary parts, logarithms...) or an expression combining
      columns (`DataFrame.eval`).
- [ ] "Recent files" menu and remembered window layout (`QSettings`).
- [ ] Clicking a history step jumps to that point (truncating redo).
- [ ] Options in the Open dialog for the reader (separator, encoding,
      header row, sheet name).

### M3 — Plotting (the "plot" in amazeplot)

- [x] `Action` base class shared by data operations and plot calls, so
      one dialog, toolbox and code preview serve both.
- [x] `PlotCall` / `AxesCall` model in the core: a matplotlib `Axes`
      method described by the same `Parameter` metadata; column
      parameters become `df['column']` references.
- [x] Figures are stacks of layers on one `Axes`, stored in the session
      snapshots, so undo/redo covers data steps and plot layers alike.
- [x] 13 plot calls (line, scatter, bar, barh, histogram, box, pie,
      area, step, stem, error bars, hexbin, heatmap) and 14 decorations
      (title, axis labels, legend, grid, scales, ranges, reference
      lines, text, tick labels, colour bar).
- [x] Plot tab with a matplotlib canvas (`FigureCanvasQTAgg`), the
      standard navigation toolbar (zoom, pan, export PNG/SVG/PDF) and a
      layer list with remove/clear.
- [x] Plots are included in the exported script
      (`fig, ax = plt.subplots()` ... `plt.show()`).
- [x] Contract test: for every plot call, the generated code draws the
      same artists as the GUI.
- [ ] Several subplots in a grid (`plt.subplots(nrows, ncols)`), with a
      target-axes selector in the dialog.
- [x] Colour bar for colour-coded layers (`fig.colorbar`).
- [x] Heatmap of a Values column on an X × Y grid (`pivot_table` +
      `pcolormesh`); hexbin cells coloured by a Values column.
- [ ] Twin y axis (`ax.twinx()`).
- [ ] Grouped plots ("one line per category" via `hue`-style splitting).
- [ ] Figure-level options: size, DPI, style sheet (`plt.style`).
- [x] Only re-render the figure when the Plot tab is visible.

### M4 — Multiple datasets

- [ ] Sessions hold several named frames (tabs).
- [ ] `merge`, `concat` and `join` operations, using a new
      `ParameterKind.DATASET`.
- [ ] Code export with one variable per dataset.

### M5 — Scale and robustness

- [x] The Data tab shows one page of rows (chosen from a bar above the
      table), so tables of millions of rows stay responsive.
- [x] New plot layers are checked on the first 1,000 rows only.
- [ ] Plot large tables from a sample (e.g. a "Sample rows" operation),
      since matplotlib needs seconds to draw millions of points.
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
| Generated code drifts from GUI behaviour | Execution and code come from the same arguments; contract tests over every operation and plot call. |
| Plot layers break after a data step removes a column | The layer is kept and the Plot tab reports which layer failed; undo or remove the layer. |
| `query` expressions are evaluated | They only run on the user's own data on their own machine, and session files will store no executable content. |
| Pickle files can run code when opened | Reading them is opt-in per file: a warning dialog, with "No" as the default, must be confirmed first. Pickles are never written. |
| pandas API changes | Pin a minimum version; CI runs the contract tests against the latest pandas. |

## 7. Definition of done (for every feature)

1. The code follows the rules in [`CLAUDE.md`](../CLAUDE.md) (PEP 8,
   typed, documented).
2. `ruff check .`, `ruff format --check .` and `python -m pytest` all pass.
3. Core logic has unit tests; GUI behaviour has at least one pytest-qt
   test.
4. User-visible behaviour is documented (README or `docs/`).
