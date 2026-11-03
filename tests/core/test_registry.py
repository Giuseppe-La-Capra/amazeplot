import pytest

from amazeplot.core.operation import MethodOperation
from amazeplot.core.registry import ActionRegistry


def _operation(key, category="C"):
    return MethodOperation(key, key.title(), category, "", method="head")


def test_register_and_get():
    registry = ActionRegistry([_operation("a")])
    assert "a" in registry
    assert registry.get("a").key == "a"
    assert len(registry) == 1


def test_duplicate_key_is_rejected():
    registry = ActionRegistry([_operation("a")])
    with pytest.raises(ValueError, match="Duplicate"):
        registry.register(_operation("a"))


def test_unknown_key():
    with pytest.raises(KeyError, match="Unknown action"):
        ActionRegistry().get("missing")


def test_by_category_preserves_order():
    registry = ActionRegistry(
        [_operation("a", "X"), _operation("b", "Y"), _operation("c", "X")]
    )
    groups = registry.by_category()
    assert list(groups) == ["X", "Y"]
    assert [op.key for op in groups["X"]] == ["a", "c"]
