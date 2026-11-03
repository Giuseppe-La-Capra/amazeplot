# amazeplot

amazeplot is a desktop application for exploring, cleaning and
summarising tabular data with **pandas** through a graphical interface.
It shows you the exact pandas code behind every click.

- Open CSV, TSV, JSON, Excel or Parquet files.
- Apply 22 DataFrame operations from a searchable list: filter, select,
  drop missing values, fill, deduplicate, rename, change types, sort,
  group and aggregate, pivot, correlate and more.
- Each operation opens a form generated from its parameters, with a
  **live preview of the pandas code** it will run.
- Undo and redo any step.
- Export the transformed data, or export the whole session as a
  **runnable Python script** that reproduces it.

## Installation

Requires Python 3.10 or newer.

```bash
pip install -e .
```

Optional file formats:

```bash
pip install -e ".[excel,parquet]"
```

On minimal Linux systems, Qt may also need system libraries such as
`libegl1`, `libgl1` and `libxkbcommon0`.

## Usage

```bash
amazeplot                 # or: python -m amazeplot
amazeplot data.csv        # open a file on start-up
```

1. **File → Open** a data file.
2. Double-click an operation in the left panel, fill in the form and
   press **OK**.
3. Watch the applied steps and the generated code in the right panel.
4. **Edit → Undo/Redo** with Ctrl+Z / Ctrl+Shift+Z.
5. **File → Export data** or **File → Export Python script**.

## Development

```bash
pip install -e ".[dev]"
ruff format .     # PEP 8 formatting, 79 columns
ruff check .      # lint
python -m pytest  # unit and GUI tests (headless)
```

The project conventions are in [`CLAUDE.md`](CLAUDE.md).

## Documentation

- [Project plan and roadmap](docs/PLAN.md)
- [Architecture](docs/architecture.md)
- [Adding a new operation](docs/adding_operations.md)

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
