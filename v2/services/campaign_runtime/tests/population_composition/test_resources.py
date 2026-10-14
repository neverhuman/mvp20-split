"""Count fixture expansion independently; per-field maxima are not a supported product."""

import pytest

from .catalog import CompositionCatalog
from .definition import campaign


def expanded_counts(body, population, batch, members=None):
    nodes, invokes = 0, 0
    for node in body["nodes"]:
        nodes += 1
        invokes += node["kind"] == "invoke"
        child_members = [None]
        if node["kind"] == "iterate":
            child_members = (list(range(0, population, batch)) if node["node_id"] == "batches"
                             else [None] * node["max_iterations"])
            child_members = [min(batch, population - i) if i is not None else None for i in child_members]
        elif node["kind"] == "scatter":
            child_members = [None] * members
        else:
            continue
        for size in child_members:
            n, i = expanded_counts(node["body"], population, batch, size)
            nodes += n
            invokes += i
    return nodes, invokes


@pytest.mark.parametrize("population,batch,generations", [(12, 1, 3), (12, 8, 3), (12, 32, 3), (1000, 32, 0), (1000, 32, 100)])
def test_resource_cost_includes_every_control_conversion_and_orchestration(population, batch, generations):
    raw = campaign(CompositionCatalog(batch), population, batch, generations)
    slices = (population + batch - 1) // batch
    rounds = generations + 1
    assert expanded_counts(raw["body"], population, batch) == (
        3 + rounds * (4 + 6 * slices + 7 * population),
        1 + rounds * (2 + 2 * slices + 4 * population))


def test_maximum_population_and_generations_exceed_existing_activation_budget():
    raw = campaign(CompositionCatalog(32), 1000, 32, 100)
    nodes, invokes = expanded_counts(raw["body"], 1000, 32)
    assert nodes == 726799 > 100000
    assert invokes == 410667
    # E2 admission must reject this combination, not truncate the graph or claim
    # the full Cartesian product of individually valid specification limits.
