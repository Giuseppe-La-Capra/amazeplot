import numpy as np
import pandas as pd
import pytest

from amazeplot.core.codegen import generate_script
from amazeplot.core.errors import OperationError
from amazeplot.core.io import load_dataframe
from amazeplot.core.session import DataSession
from amazeplot.operations.create import (
    APPLY_FUNCTION,
    CALCULATE_COLUMN,
    FUNCTIONS,
)
from amazeplot.operations.select import HEAD


@pytest.fixture
def signal():
    return pd.DataFrame({"value": np.array([3 + 4j, -2j, np.nan])})


def _run_code(operation, params, frame):
    """Execute the generated code, with its imports, on a copy."""
    resolved = operation.resolve_params(params, frame.columns.tolist())
    namespace = {"pd": pd, "df": frame.copy()}
    exec("\n".join(operation.code_imports), namespace)
    exec(operation.to_code(resolved), namespace)
    return namespace["df"]


def test_magnitude_and_phase_of_complex_column(signal):
    result = APPLY_FUNCTION.apply(
        signal, {"column": "value", "function": "Absolute value (magnitude)"}
    )
    result = APPLY_FUNCTION.apply(
        result, {"column": "value", "function": "Phase (degrees)"}
    )
    assert list(result.columns) == ["value", "value_abs", "value_phase_deg"]
    assert result["value_abs"].tolist()[:2] == [5.0, 2.0]
    assert result["value_phase_deg"].iloc[1] == pytest.approx(-90.0)
    assert np.isnan(result["value_abs"].iloc[2])  # Missing stays missing.


@pytest.mark.parametrize("function", list(FUNCTIONS))
def test_every_function_matches_its_code(signal, function):
    params = {"column": "value", "function": function}
    with np.errstate(all="ignore"):  # log of 0 etc.: same in both paths
        expected = APPLY_FUNCTION.apply(signal, params)
        pd.testing.assert_frame_equal(
            _run_code(APPLY_FUNCTION, params, signal), expected
        )


def test_custom_name_and_code(signal):
    params = {
        "column": "value",
        "function": "Phase (radians)",
        "new_name": "phase",
    }
    resolved = APPLY_FUNCTION.resolve_params(params, ["value"])
    assert APPLY_FUNCTION.to_code(resolved) == (
        "df = df.assign(**{'phase': np.angle(df['value'])})"
    )
    assert "phase" in APPLY_FUNCTION.apply(signal, params).columns


def test_calculate_column(people):
    params = {"name": "score per year", "expression": "score / age * 10"}
    result = CALCULATE_COLUMN.apply(people, params)
    assert result["score per year"].iloc[0] == pytest.approx(7.5 / 31 * 10)
    pd.testing.assert_frame_equal(
        _run_code(CALCULATE_COLUMN, params, people), result
    )


def test_calculate_column_reports_bad_expressions(people):
    with pytest.raises(OperationError, match="Calculate column failed"):
        CALCULATE_COLUMN.apply(people, {"name": "x", "expression": "nope +"})


def test_script_imports_numpy_only_when_needed(signal, tmp_path):
    path = tmp_path / "signal.pkl"  # Pickle keeps the complex dtype.
    signal.to_pickle(path)
    session = DataSession()
    session.load(*load_dataframe(path))
    session.apply(HEAD, {})
    assert "import numpy" not in generate_script(session)

    session.apply(
        APPLY_FUNCTION, {"column": "value", "function": "Phase (radians)"}
    )
    script = generate_script(session)
    assert script.index("import numpy as np") < script.index(
        "import pandas as pd"
    )
    namespace = {}
    exec(script, namespace)
    pd.testing.assert_frame_equal(namespace["df"], session.frame)
