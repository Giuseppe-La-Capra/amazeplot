import pandas as pd
import pytest

from amazeplot.core.codegen import generate_script
from amazeplot.core.errors import DataIOError
from amazeplot.core.io import load_dataframe, save_dataframe
from amazeplot.core.session import DataSession
from amazeplot.operations.clean import DROPNA
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
        load_dataframe(tmp_path / "data.pkl")
    with pytest.raises(DataIOError, match="Unsupported"):
        save_dataframe(pd.DataFrame(), tmp_path / "data.pkl")


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
