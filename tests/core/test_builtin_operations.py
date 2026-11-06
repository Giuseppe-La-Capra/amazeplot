"""Contract tests run against every built-in data operation.

Every operation declares an ``example`` in the catalogue. The tests run
it to check that it applies cleanly and that its generated code
reproduces exactly what the GUI computed.
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


def test_every_operation_has_an_example():
    assert [op.key for op in OPERATIONS if op.example is None] == []


def test_operation_metadata_is_complete():
    for operation in OPERATIONS:
        assert operation.label, operation.key
        assert operation.category, operation.key
        assert operation.description, operation.key


@pytest.mark.parametrize("operation", OPERATIONS, ids=lambda op: op.key)
def test_generated_code_reproduces_result(operation: Operation, people):
    params = operation.example
    result = operation.apply(people, params)

    resolved = operation.resolve_params(params, people.columns.tolist())
    namespace = {"pd": pd, "df": people.copy()}
    exec(operation.to_code(resolved), namespace)

    pd.testing.assert_frame_equal(namespace["df"], result)


@pytest.mark.parametrize("operation", OPERATIONS, ids=lambda op: op.key)
def test_operation_does_not_mutate_input(operation: Operation, people):
    before = people.copy()
    operation.apply(people, operation.example)
    pd.testing.assert_frame_equal(people, before)
