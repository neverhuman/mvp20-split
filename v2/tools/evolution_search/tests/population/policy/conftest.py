import pytest
from amphora_evolution_search.population import OriginalPopulation


@pytest.fixture
def population_original(population_original, request):
    record = population_original.record
    if getattr(request, "param", None) == "one_parent":
        record = record.model_copy(update={"selection": record.selection.model_copy(update={"minimum_parents": 1})})
    if getattr(request, "param", None) == "optional":
        method = record.method_graph.methods[0].model_copy(update={"method_id": "annotation", "node_path": ("evaluate", "annotation"), "required": False})
        record = record.model_copy(update={"method_graph": record.method_graph.model_copy(update={"methods": (*record.method_graph.methods, method)})})
    return OriginalPopulation(record)
