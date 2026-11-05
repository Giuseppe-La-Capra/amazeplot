# amazeplot

amazeplot is a desktop application for exploring, cleaning, summarising
and **plotting** tabular data with **pandas** and **matplotlib** through
a graphical interface. It shows you the exact code behind every click.

- Open CSV, TSV, JSON, Excel or Parquet files.
- Apply 22 DataFrame operations from a searchable toolbox: filter,
  select, drop missing values, fill, deduplicate, rename, change types,
  sort, group and aggregate, pivot, correlate and more.
- Plot anything in the table with 13 matplotlib plot types: line,
  scatter, bar, horizontal bar, histogram, box, pie, area, step, stem,
  error bars, hexbin and heatmap.
- Decorate the figure with titles, axis labels, a legend, a grid, log
  scales, axis ranges, reference lines, text and rotated tick labels.
- Plots are built from **layers** drawn on top of each other, so you can
  combine, for example, a scatter, a reference line and a legend.
- Every action opens a form generated from its parameters, with a
  **live preview of the pandas or matplotlib code** it will run.
- Undo and redo any step, whether it changed the data or the plot.
- Zoom, pan and save the figure as PNG, SVG or PDF from the plot
  toolbar.
- Export the transformed data, or export the whole session (data steps
  and figure) as a **runnable Python script** that reproduces it.

## Getting started

### 1. Requirements

- Python 3.10 or newer (`python --version`).
- Windows, macOS or Linux with a desktop. amazeplot is a desktop
  application, so it opens a window.

### 2. Get the code

```bash
git clone https://github.com/Giuseppe-La-Capra/amazeplot.git
```

```bash
cd amazeplot
```

### 3. Create a virtual environment (recommended)

A virtual environment keeps amazeplot's dependencies (pandas,
matplotlib, PySide6) separate from your other Python projects.

```bash
python -m venv .venv
```

Activate it on Linux or macOS:

```bash
source .venv/bin/activate
```

Activate it on Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

Activate it again whenever you open a new terminal to use amazeplot.

### 4. Install

```bash
pip install -e .
```

To also read and write Excel (`.xlsx`) and Parquet files:

```bash
pip install -e ".[excel,parquet]"
```

### 5. Run

```bash
amazeplot
```

`python -m amazeplot` does the same thing. To open a file on start-up,
pass its path:

```bash
amazeplot path/to/data.csv
```

No data at hand? This command writes a small `demo.csv` to try:

```bash
python -c "import pandas as pd, numpy as np; rng = np.random.default_rng(0); pd.DataFrame({'city': rng.choice(['Rome', 'Oslo', 'Lima'], 200), 'age': rng.integers(18, 80, 200), 'score': rng.normal(7, 1.5, 200).round(1)}).to_csv('demo.csv', index=False)"
```

```bash
amazeplot demo.csv
```

### Troubleshooting

- **`amazeplot: command not found`**: the virtual environment isn't
  active. Activate it (step 3), or run `python -m amazeplot`.
- **Linux: "Could not load the Qt platform plugin"** or a missing
  `libEGL.so.1`: install the system libraries Qt needs. On
  Debian/Ubuntu:

  ```bash
  sudo apt-get install libegl1 libgl1 libxkbcommon0 libxcb-cursor0 libfontconfig1 libdbus-1-3
  ```

- **Opening an `.xlsx` or `.parquet` file fails** with a message about a
  missing module: install the optional extras (step 4).

## Usage

1. **File → Open** a data file.
2. Double-click an action in the **Toolbox** on the left, fill in the
   form and press **OK**.
   - The *Select*, *Clean*, *Transform* and *Aggregate* categories change
     the data, and the **Data** tab shows the result.
   - The *Plot* category adds a layer to the figure, and the **Plot** tab
     shows it. The *Decorate* category adds titles, labels, a legend and
     so on. Layers are drawn in order: remove or clear them from the list
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
