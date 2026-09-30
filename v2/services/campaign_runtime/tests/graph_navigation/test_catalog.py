"""Named-view capabilities are implemented Runtime reads, scoped to an authorized cut."""

from dataclasses import replace

import pytest
from amphora_campaign_runtime.graph_navigation.catalog import RuntimeViewCatalog
from amphora_campaign_runtime.inspection.cursors import InspectionError
from amphora_contracts_core import Scope

from ..graph_inspection.test_snapshots import start


def test_catalog_pins_owner_filters_bounds_and_read_scope(graph_env):
    graph = graph_env
    run, cursors, snapshots = start(graph)
    observation = snapshots.page(graph.env.principal, run).snapshot
    catalog = RuntimeViewCatalog(graph.env.engine, cursors)
    result = catalog.read(graph.env.principal, run, observation.snapshot_token)
    assert result.cut == observation.cut
    assert [view.view_id for view in result.views] == ["execution_topology", "successor_lineage"]
    topology, lineage = result.views
    assert topology.result_bound == 256 and lineage.result_bound == 64
    assert [(field.name, field.kind) for field in topology.filters] == [
        ("scope_key", "digest"), ("focus_activation_id", "digest"), ("radius", "integer")]
    assert lineage.filters == ()
    assert {view.owner for view in result.views} == {"campaign-runtime"}
    with pytest.raises(InspectionError):
        catalog.read(replace(graph.env.principal, scope=Scope(tenant_id="other", project_id="other")), run, observation.snapshot_token)
    with pytest.raises(InspectionError):
        catalog.read(graph.env.principal, run, "invalid-snapshot")
