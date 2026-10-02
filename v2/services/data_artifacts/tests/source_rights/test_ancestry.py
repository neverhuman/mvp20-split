import pytest
from amphora_data_artifacts.source_rights.ancestry import MAX_ARTIFACTS, traverse
from amphora_data_artifacts.source_rights.model import RightsError


def test_shared_ancestor_is_not_a_cycle():
    graph = {"root": ("left", "right"), "left": ("base",), "right": ("base",)}
    assert traverse(("root",), lambda key: graph.get(key, ())) == ("base", "left", "right", "root")


@pytest.mark.parametrize("graph", [{"a": ("a",)}, {"a": ("b",), "b": ("a",)}])
def test_cycles_fail_closed(graph):
    with pytest.raises(RightsError, match="rights_lineage_cycle"):
        traverse(("a",), lambda key: graph.get(key, ()))


def test_limits_and_deep_chain_do_not_use_python_recursion():
    assert len(traverse((0,), lambda i: (i + 1,) if i < MAX_ARTIFACTS - 1 else ())) == MAX_ARTIFACTS
    with pytest.raises(RightsError, match="rights_lineage_limit"):
        traverse((0,), lambda i: (i + 1,))
    with pytest.raises(RightsError, match="rights_lineage_limit"):
        traverse((0,), lambda i: tuple(range(1, 130)))
