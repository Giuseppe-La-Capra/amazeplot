# amazeplot

amazeplot is a desktop application for exploring, cleaning, summarising
and **plotting** tabular data with **pandas** and **matplotlib** through
a graphical interface. It shows you the exact code behind every click.

- Open CSV, TSV, JSON, Excel, Parquet or pickle (`.pkl`) files. Pickles
  can run code when opened, so amazeplot asks you to confirm first.
- Multi-level row and column labels (pandas MultiIndex) are shown as
  `7570.0 | 0 | 0`; **Flatten column names** and **Reset index** turn
  them into simple columns.
- Complex numbers are supported. CSV files store them as text such as
  `(1+2j)`, so amazeplot converts those columns back when opening the
  file (an undoable step).
- An info panel under the table shows the type and statistics of the
  selected column and every value of the selected row.
- **Create columns** from other columns: apply a function (absolute
  value and phase of complex numbers, real/imaginary parts, square root,
  logarithms...) or calculate an expression such as `score / age * 100`.
- Apply 25 DataFrame operations from a searchable toolbox: filter,
  select, drop missing values, fill, deduplicate, rename, change types,
  sort, group and aggregate, pivot, correlate and more.
- Plot anything in the table with 13 matplotlib plot types: line,
  scatter, bar, horizontal bar, histogram, box, pie, area, step, stem,
  error bars, hexbin and heatmap. Every plot asks which columns to use
  (X, Y, values...). The heatmap lays a Values column out on an X × Y
  grid; hexbin cells can show counts or the mean of a Values column.
- Decorate the figure with titles, axis labels, a legend, a grid, log
  scales, axis ranges, reference lines, text, rotated tick labels and a
  colour bar for colour-coded plots. Heatmaps, hexbins and colour-coded
  scatters can add their colour bar for you, as its own layer.
- Plots are built from **layers** drawn on top of each other, so you can
  combine, for example, a scatter, a reference line and a legend.
- Every action opens a form generated from its parameters, with a
  **live preview of the pandas or matplotlib code** it will run.
- Undo and redo any step, whether it changed the data or the plot.
- Zoom, pan and save the figure as PNG, SVG or PDF from the plot
  toolbar.
- Export the transformed data, or export the whole session (data steps
  and figure) as a **runnable Python script** that reproduces it.
- Built-in **help** (F1): a worked example to follow, then a page for
  every tool with its options, an example and a link to the pandas or
  matplotlib documentation.

## Getting started

amazeplot is a desktop application, so it needs Python 3.10 or newer
and a computer with a graphical desktop: it opens a window. Follow the
section for your operating system, then [try it](#try-it).

### Linux

The commands below are for Debian and Ubuntu. On other distributions,
install the equivalent packages with your package manager.

1. Install Python, Git and the system libraries Qt needs to open
   windows:

   ```bash
   sudo apt-get update
   ```

   ```bash
   sudo apt-get install python3 python3-venv git libegl1 libgl1 libxkbcommon0 libxcb-cursor0 libfontconfig1 libdbus-1-3
   ```

2. Get the code:

   ```bash
   git clone https://github.com/Giuseppe-La-Capra/amazeplot.git
   ```

   ```bash
   cd amazeplot
   ```

3. Create and activate a virtual environment. It keeps amazeplot's
   dependencies (pandas, matplotlib, PySide6) separate from the rest of
   your system:

   ```bash
   python3 -m venv .venv
   ```

   ```bash
   source .venv/bin/activate
   ```

4. Install amazeplot:

   ```bash
   pip install -e .
   ```

5. Start it:

   ```bash
   amazeplot
   ```

Next time, open a terminal in the `amazeplot` folder and run
`source .venv/bin/activate` before `amazeplot`.

### Windows

1. Install [Python](https://www.python.org/downloads/) (tick **Add
   python.exe to PATH** in the installer) and
   [Git](https://git-scm.com/download/win).

2. Open **PowerShell** and get the code:

   ```powershell
   git clone https://github.com/Giuseppe-La-Capra/amazeplot.git
   ```

   ```powershell
   cd amazeplot
   ```

3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   ```

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell refuses to run the activation script, allow local
   scripts for your user once, then activate again:

   ```powershell
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   ```

4. Install amazeplot:

   ```powershell
   pip install -e .
   ```

5. Start it:

   ```powershell
   amazeplot
   ```

Next time, open PowerShell in the `amazeplot` folder and run
`.venv\Scripts\Activate.ps1` before `amazeplot`.

### macOS

Install Python 3 from [python.org](https://www.python.org/downloads/)
or Homebrew, then follow the Linux steps 2 to 5. No extra system
libraries are needed.

### Updating

`pip install -e .` installs amazeplot in *editable* mode: Python runs
the code straight from your `amazeplot` folder. After pulling new
commits you normally **don't need to reinstall**. Pull, then restart
amazeplot:

```bash
git pull
```

The exception is an update that adds or changes dependencies, which are
listed in `pyproject.toml`. Then run the install again, with the
virtual environment active. It's quick and safe to run after any
update, so if in doubt, run it:

```bash
pip install -e .
```

If you installed the optional extras, include them again:
`pip install -e ".[excel,parquet]"`.

### Try it

With the virtual environment active, `python -m amazeplot` works the
same as `amazeplot`. To open a file on start-up, pass its path:

```bash
amazeplot path/to/data.csv
```

No data at hand? Choose **Help → Open example data** for a small table
of people, then **Help → amazeplot Help** (F1) and follow the worked
example on the first page.

To also read and write Excel (`.xlsx`) and Parquet files, install the
optional extras:

```bash
pip install -e ".[excel,parquet]"
```

### Troubleshooting

- **`amazeplot: command not found`** (or "not recognized" on Windows):
  the virtual environment isn't active. Activate it (step 3), or run
  `python -m amazeplot`.
- **Linux: "Could not load the Qt platform plugin"** or a missing
  `libEGL.so.1`: the Qt system libraries from Linux step 1 are missing.
- **Linux: `python3 -m venv` fails** saying `ensurepip` is not
  available: install `python3-venv` (Linux step 1).
- **A pickle (`.pkl`) file asks for confirmation:** a pickle can run any
  code on your computer when it is opened, so only open pickles you
  created yourself or fully trust. amazeplot can open a pickle only if
  it holds a pandas DataFrame, not some other Python object.
- **Opening an `.xlsx` or `.parquet` file fails** with a message about a
  missing module: install the optional extras (see [Try it](#try-it)).

## Usage

**Help → amazeplot Help** (F1) opens the built-in help. Its first page
walks through a complete example; the other pages describe every tool.
Each tool's form also has a **Help** button that opens its page.

1. **File → Open** a data file, or **Help → Open example data**. The
   **Data** tab shows the table one page at a time, so even millions of
   rows stay responsive. Use the bar above the table to choose the first
   row (**Rows from**), the **Rows per page** (100 to 100,000), or move
   with **Previous** and **Next**. Tools always work on the whole table,
   not just the visible page.

   Click any cell to see details in the **info panel** under the table
   (drag its top edge to resize it):
   - **Column**: name, type (dtype), number of values and missing values,
     unique values, memory, and statistics such as minimum, maximum and
     mean, computed over the whole table.
   - **Row**: position, label (with the level names of a multi-level
     index) and every value in full, handy when a column is too narrow.
2. Double-click an action in the **Toolbox** on the left, fill in the
   form and press **OK**.
   - The *Select*, *Clean*, *Create*, *Transform* and *Aggregate*
     categories change the data, and the **Data** tab shows the result.
     *Create* adds new columns, e.g. the magnitude and phase of a complex
     column, or an expression such as `score / age`.
   - The *Plot* category adds a layer to the figure, and the **Plot** tab
     shows it. Each plot asks which columns to use. The *Decorate*
     category adds titles, labels, a legend, a colour bar and so on. Layers are drawn in order: remove or clear them from the list
     beside the figure.
3. Watch the applied steps and the generated code in the right panel.
4. **Edit → Undo/Redo** with Ctrl+Z / Ctrl+Shift+Z.
5. **File → Export data** or **File → Export Python script**. Use the
   disk icon on the plot toolbar to save the figure.

For example, these five toolbox actions (Group and aggregate, then Bar
chart, Title, Y axis label and Tick labels) export as:

```python
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('people.csv')
df = df.groupby(['city'], as_index=False)[['score']].agg('mean')

fig, ax = plt.subplots()
ax.bar(df['city'], df['score'])
ax.set_title('Mean score per city')
ax.set_ylabel('Score')
ax.tick_params(axis='x', labelrotation=45.0)
plt.show()
```

## Development

Install the development tools into the activated virtual environment,
then format, lint and test:

```bash
pip install -e ".[dev]"
```

```bash
ruff format .     # PEP 8 formatting, 79 columns
ruff check .      # lint
python -m pytest  # unit and GUI tests (headless, no window opens)
```

The project conventions are in [`CLAUDE.md`](CLAUDE.md).

## Documentation

- [Project plan and roadmap](docs/PLAN.md)
- [Architecture](docs/architecture.md)
- [Adding a new operation or plot](docs/adding_operations.md)

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
