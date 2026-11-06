import warnings

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from amazeplot.core.codegen import generate_script
from amazeplot.core.errors import DataIOError
from amazeplot.core.io import (
    executes_code_on_read,
    load_dataframe,
    save_dataframe,
)
from amazeplot.core.session import DataSession
from amazeplot.operations.clean import DROPNA
from amazeplot.operations.decorate import TITLE
from amazeplot.operations.plot import SCATTER
from amazeplot.operations.transform import SORT_VALUES


@pytest.mark.parametrize("suffix", [".csv", ".tsv", ".json"])
def test_round_trip(people, tmp_path, suffix):
    path = tmp_path / f"people{suffix}"
    save_dataframe(people, path)
    loaded, source = load_dataframe(path)
    assert source.path == path
    pd.testing.assert_frame_equal(loaded, people, check_dtype=False)


def test_unsupported_extension(tmp_path):
    with pytest.raises(DataIOError, match="Unsupported"):
        load_dataframe(tmp_path / "data.xyz")
    with pytest.raises(DataIOError, match="Unsupported"):
        save_dataframe(pd.DataFrame(), tmp_path / "data.xyz")


@pytest.mark.parametrize("suffix", [".pkl", ".pickle", ".PKL"])
def test_pickle_is_read_and_flagged_unsafe(people, tmp_path, suffix):
    path = tmp_path / f"people{suffix}"
    people.to_pickle(path, compression=None)
    assert executes_code_on_read(path)
    loaded, source = load_dataframe(path)
    assert source.to_code() == f"df = pd.read_pickle({str(path)!r})"
    pd.testing.assert_frame_equal(loaded, people)


@pytest.mark.parametrize("name", ["data.csv", "data.parquet", "data"])
def test_other_formats_are_safe(name):
    assert not executes_code_on_read(name)


def test_pickle_without_a_dataframe(people, tmp_path):
    path = tmp_path / "series.pkl"
    people["age"].to_pickle(path)
    with pytest.raises(DataIOError, match="Series, not a DataFrame"):
        load_dataframe(path)


def test_corrupt_pickle(tmp_path):
    path = tmp_path / "broken.pkl"
    path.write_text("this is not a pickle")
    with pytest.raises(DataIOError, match="Cannot read"):
        load_dataframe(path)


def test_script_reloads_pickle(people, tmp_path):
    path = tmp_path / "people.pkl"
    people.to_pickle(path)
    session = DataSession()
    session.load(*load_dataframe(path))
    session.apply(DROPNA, {})
    namespace = {}
    exec(generate_script(session), namespace)
    pd.testing.assert_frame_equal(namespace["df"], session.frame)


def test_missing_file(tmp_path):
    with pytest.raises(DataIOError, match="Cannot read"):
        load_dataframe(tmp_path / "missing.csv")


def test_generated_script_reproduces_session(people, tmp_path):
    path = tmp_path / "people.csv"
    save_dataframe(people, path)
    session = DataSession()
    session.load(*load_dataframe(path))
    session.apply(DROPNA, {})
    session.apply(SORT_VALUES, {"by": ["score"], "ascending": False})

    script = generate_script(session)
    namespace = {}
    exec(script, namespace)

    pd.testing.assert_frame_equal(namespace["df"], session.frame)


def test_script_without_source_has_placeholder():
    session = DataSession()
    session.load(pd.DataFrame({"a": [1]}))
    assert "TODO" in generate_script(session)


def test_script_rejects_invalid_variable():
    with pytest.raises(ValueError):
        generate_script(DataSession(), variable="not valid")


def test_script_without_plot_does_not_import_pyplot(people):
    session = DataSession()
    session.load(people)
    assert "matplotlib" not in generate_script(session)


def test_generated_script_draws_the_figure(people, tmp_path):
    path = tmp_path / "people.csv"
    save_dataframe(people, path)
    session = DataSession()
    session.load(*load_dataframe(path))
    session.apply(DROPNA, {})
    session.add_layer(SCATTER, {"x": "age", "y": "score"})
    session.add_layer(TITLE, {"label": "People"})

    script = generate_script(session)
    assert script.index("import matplotlib") < script.index("import pandas")

    namespace = {}
    plt.close("all")
    with warnings.catch_warnings():
        # plt.show() warns that the Agg test backend is non-interactive.
        warnings.simplefilter("ignore", UserWarning)
        exec(script, namespace)
    axes = namespace["ax"]
    assert axes.get_title() == "People"
    assert len(axes.collections[0].get_offsets()) == len(session.frame)
    plt.close("all")
