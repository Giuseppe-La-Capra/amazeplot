import pandas as pd
import pytest

from amazeplot.core.errors import DataIOError
from amazeplot.core.examples import (
    EXAMPLE_COLUMNS,
    EXAMPLE_FILE_NAME,
    example_data,
    write_example_data,
)
from amazeplot.core.io import load_dataframe
from amazeplot.core.operation import Operation
from amazeplot.core.plotting import Layer, PlotCall
from amazeplot.operations import build_default_registry
from amazeplot.operations.plot import SCATTER

ACTIONS = list(build_default_registry())


def test_example_data_shape():
    frame = example_data()
    assert tuple(frame.columns) == EXAMPLE_COLUMNS
    assert frame.isna().any().any()
    assert frame.duplicated().any()


def test_example_data_is_a_fresh_copy():
    first = example_data()
    first.loc[0, "name"] = "changed"
    assert example_data().loc[0, "name"] == "Ann"


def test_write_example_data(tmp_path):
    path = write_example_data(tmp_path / "new" / "dir")
    assert path.name == EXAMPLE_FILE_NAME
    loaded, _ = load_dataframe(path)
    expected = example_data()
    # CSV stores a missing value as empty, which reads back as NaN.
    expected = expected.where(expected.notna(), float("nan"))
    pd.testing.assert_frame_equal(loaded, expected, check_dtype=False)


def test_write_example_data_reports_errors(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    with pytest.raises(DataIOError):
        write_example_data(blocker / "sub")


@pytest.mark.parametrize("action", ACTIONS, ids=lambda action: action.key)
def test_every_example_runs_on_the_example_data(action):
    # The help pages show each example applied to this table.
    frame = example_data()
    params = action.resolve_params(action.example, frame.columns.tolist())
    if isinstance(action, Operation):
        action.execute(frame, params)
    else:
        assert isinstance(action, PlotCall)
        # Decorations such as the colour bar build on an earlier layer.
        coloured = Layer(SCATTER, {"x": "age", "y": "score", "c": "score"})
        action.check(frame, params, previous=(coloured,))
