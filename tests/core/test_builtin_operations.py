"""Contract tests run against every built-in data operation.

When you add an operation, add an entry to ``EXAMPLES``: the tests then
check that it applies cleanly and that its generated code reproduces
exactly what the GUI computed.
"""

import pandas as pd
import pytest

from amazeplot.core.operation import Operation
from amazeplot.operations import build_default_registry

OPERATIONS = [
    action
    for action in build_default_registry()
    if isinstance(action, Operation)
]

EXAMPLES = {
    "head": {"n": 2},
    "tail": {"n": 2},
    "query": {"expr": "score > 7"},
    "select_columns": {"items": ["name", "age"]},
    "drop_columns": {"columns": ["city"]},
    "nlargest": {"n": 2, "columns": ["score"]},
    "nsmallest": {"n": 2, "columns": ["score"]},
    "dropna": {"how": "any", "subset": ["age"]},
    "fillna": {"value": "0", "column": "age"},
    "drop_duplicates": {"keep": False},
    "rename_column": {"column": "age", "new_name": "years"},
    "astype": {"column": "score", "dtype": "string"},
    "replace": {"to_replace": "'Rome'", "value": "'Roma'"},
    "sort_values": {"by": ["age"], "ascending": False},
    "set_index": {"keys": ["name"]},
    "reset_index": {"drop": True},
    "transpose": {},
    "groupby": {"by": ["city"], "columns": ["score"], "func": "mean"},
    "describe": {},
    "value_counts": {"subset": ["city"]},
    "pivot_table": {"index": ["city"], "values": ["score"]},
    "corr": {"numeric_only": True},
}


def test_every_operation_has_an_example():
    assert {op.key for op in OPERATIONS} == set(EXAMPLES)


def test_operation_metadata_is_complete():
    for operation in OPERATIONS:
        assert operation.label, operation.key
        assert operation.category, operation.key
        assert operation.description, operation.key


@pytest.mark.parametrize("operation", OPERATIONS, ids=lambda op: op.key)
def test_generated_code_reproduces_result(operation: Operation, people):
    params = EXAMPLES[operation.key]
    result = operation.apply(people, params)

    resolved = operation.resolve_params(params, people.columns.tolist())
    namespace = {"pd": pd, "df": people.copy()}
    exec(operation.to_code(resolved), namespace)

    pd.testing.assert_frame_equal(namespace["df"], result)


@pytest.mark.parametrize("operation", OPERATIONS, ids=lambda op: op.key)
def test_operation_does_not_mutate_input(operation: Operation, people):
    before = people.copy()
    operation.apply(people, EXAMPLES[operation.key])
    pd.testing.assert_frame_equal(people, before)
