import copy
import json
from pathlib import Path

import pytest
from amphora_agent_planning.research_view_access import (
    ResearchViewReader,
    ResearchViewTransport,
    ResearchViewWindow,
    ViewPage,
    ViewSelection,
)
from amphora_agent_planning.research_view_access.page import catalog
from amphora_agent_planning.research_view_access.query import VIEWS
from amphora_contracts_research_views import ResearchViewCatalog, research_view_schema

from ..campaign_context.test_selection import SCOPE, request
from ..knowledge_access.test_transport import peer  # noqa: F401

NAMES = {"specimens": "specimen", "properties": "property", "observation_series": "series"}


def inputs(view="specimens"):
    data = json.loads((Path(__file__).parent / "fixtures/views.json").read_bytes())
    # Fixture provenance is the public Research Views contract corpus. Adapt only
    # scope; recompute query identity because exact scope participates in it.
    def scope(value):
        if isinstance(value, dict):
            if set(value) == {"tenant_id", "project_id"}:
                value.update(SCOPE.model_dump())
            else:
                for item in value.values():
                    scope(item)
        elif isinstance(value, list):
            for item in value:
                scope(item)
    scope(data)
    name = NAMES[view]
    query = VIEWS[view][0].model_validate_json(json.dumps(data[name + "_request"]))
    selection = ViewSelection.bind(query, request())
    page = data[name + "_page"]
    page["query_sha256"] = selection.query_sha256
    if page["next_position"]:
        page["next_position"]["query_sha256"] = selection.query_sha256
    return selection, page, data


def page_model(selection, value):
    return VIEWS[selection.view][1].model_validate_json(json.dumps(value))


@pytest.mark.parametrize("view", NAMES)
def test_exact_page_keeps_every_reported_field_and_owns_immutable_bytes(view):
    selected, raw, _ = inputs(view)
    page = ViewPage.bind(selected, page_model(selected, raw))
    assert page.document().model_dump(mode="json") == raw
    assert len(page.sha256) == len(selected.sha256) == 64
    raw["total"] += 1
    assert page.document().total != raw["total"]
    assert ViewSelection.bind(selected.document(), selected.request) == selected


@pytest.mark.parametrize("view", NAMES)
def test_query_hash_matches_literal_public_contract_vector(view):
    data = json.loads((Path(__file__).parent / "fixtures/views.json").read_bytes())
    original = request().document().model_dump(mode="json")
    # Change all request scopes to public fixture scope, not peer-private code.
    raw = json.dumps(original).replace('"tenant_id": "planning-fixture"', '"tenant_id": "fixture"').replace(
        '"project_id": "context"', '"project_id": "materials"')
    from amphora_agent_planning.context import RequestSnapshot
    from amphora_contracts_core import Scope
    context = RequestSnapshot.from_bytes(raw.encode(), actor_id="fixture", scope=Scope(tenant_id="fixture", project_id="materials"))
    query = VIEWS[view][0].model_validate_json(json.dumps(data[NAMES[view] + "_request"]))
    selected = ViewSelection.bind(query, context)
    assert selected.query_sha256 == data[NAMES[view] + "_page"]["query_sha256"]


@pytest.mark.parametrize("field,value,code", [
    ("query_sha256", "f" * 64, "identity"), ("total", 2, "window"),
    ("rows", [], "window"), ("next_position", {"query_sha256": "f" * 64, "offset": 1}, "continuation"),
])
def test_rejects_misbound_or_incomplete_pages(field, value, code):
    selected, raw, _ = inputs()
    raw[field] = value
    with pytest.raises(ValueError, match="research_view_" + code):
        ViewPage.bind(selected, page_model(selected, raw))


def test_foreign_nested_source_scope_is_rejected():
    selected, raw, _ = inputs("properties")
    raw["rows"][0]["source"]["scope"]["project_id"] = "other"
    with pytest.raises(ValueError, match="research_view_scope"):
        ViewPage.bind(selected, page_model(selected, raw))


def test_property_selection_order_and_total_are_not_owner_discretion():
    selected, raw, _ = inputs("properties")
    raw["rows"][0]["reference"]["observation_id"] = "substituted"
    with pytest.raises(ValueError, match="research_view_observations"):
        ViewPage.bind(selected, page_model(selected, raw))


def test_sample_identity_and_material_binding_do_not_collapse_candidates():
    selected, raw, _ = inputs()
    raw["rows"].append(copy.deepcopy(raw["rows"][0]))
    raw["total"] = 2
    with pytest.raises(ValueError, match="research_view_duplicate_sample"):
        ViewPage.bind(selected, page_model(selected, raw))
    raw["rows"][1]["sample"]["reference"]["sample_id"] = "distinct-preparation"
    assert len(ViewPage.bind(selected, page_model(selected, raw)).document().rows) == 2
    raw["rows"][0]["material"]["reference"]["revision"] += 1
    with pytest.raises(ValueError, match="research_view_material"):
        ViewPage.bind(selected, page_model(selected, raw))
    raw["rows"][0]["material"] = None
    assert ViewPage.bind(selected, page_model(selected, raw)).document().rows[0].material is None


def test_explicit_terminal_empty_page_and_foreign_position():
    selected, raw, _ = inputs()
    query = selected.document().model_dump(mode="json")
    query["position"] = {"query_sha256": selected.query_sha256, "offset": 1}
    chosen = ViewSelection.bind(VIEWS[selected.view][0].model_validate_json(json.dumps(query)), selected.request)
    assert chosen.query_sha256 == selected.query_sha256 and chosen.sha256 != selected.sha256
    raw.update(request=query, rows=[])
    assert ViewPage.bind(chosen, page_model(chosen, raw)).document().rows == ()
    query["position"]["offset"] = 2
    chosen = ViewSelection.bind(VIEWS[selected.view][0].model_validate_json(json.dumps(query)), selected.request)
    raw["request"] = query
    with pytest.raises(ValueError, match="research_view_window"):
        ViewPage.bind(chosen, page_model(chosen, raw))
    query["position"]["query_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="research_view_position"):
        ViewSelection.bind(VIEWS[selected.view][0].model_validate_json(json.dumps(query)), selected.request)


def test_duplicate_selected_observations_and_foreign_scope():
    selected, _, _ = inputs("properties")
    query = selected.document()
    with pytest.raises(ValueError, match="research_view_duplicate_observation"):
        ViewSelection.bind(query.model_copy(update={"observations": query.observations * 2}), selected.request)
    changed = query.experiment.model_copy(update={"scope": SCOPE.model_copy(update={"project_id": "other"})})
    with pytest.raises(ValueError, match="research_view_scope"):
        ViewSelection.bind(query.model_copy(update={"experiment": changed}), selected.request)
    with pytest.raises(ValueError, match="research_view_query_type"):
        ViewSelection.bind(changed, selected.request)


@pytest.mark.parametrize("change,code", [("duplicate", "catalog"), ("schema", "schema"), ("experiment", "identity")])
def test_catalog_requires_exact_capabilities_schema_pins_and_experiment(change, code):
    selected, _, data = inputs()
    raw = data["catalog"]
    for entry in raw["views"]:
        entry["result_schema"] = research_view_schema(entry["view_id"]).model_dump(mode="json")
    valid = ResearchViewCatalog.model_validate_json(json.dumps(raw))
    assert catalog(valid, selected.document().experiment) == valid
    if change == "duplicate":
        raw["views"][1] = raw["views"][0]
    elif change == "schema":
        raw["views"][0]["result_schema"]["sha256"] = "f" * 64
    else:
        raw["experiment"]["revision"] += 1
    with pytest.raises(ValueError, match="research_view_" + code):
        catalog(ResearchViewCatalog.model_validate_json(json.dumps(raw)), selected.document().experiment)


@pytest.mark.parametrize("view", NAMES)
def test_real_http_uses_one_exact_authenticated_page_without_following_next(peer, view):  # noqa: F811
    server, _, _ = peer
    selected, raw, _ = inputs(view)
    server.body = json.dumps(raw).encode()
    reader = ResearchViewReader(ResearchViewTransport(f"http://127.0.0.1:{server.server_port}", "t" * 32))
    result = reader.read(selected)
    assert result.failure is None and result.page.document() == page_model(selected, raw)
    assert result.calls == 1 and result.bytes == len(server.body)
    assert server.calls == [(VIEWS[view][2], "Bearer " + "t" * 32, selected.document().model_dump(mode="json"))]


@pytest.mark.parametrize("status,code", [(403, "access_denied"), (404, "reference_unavailable"), (503, "peer_unavailable")])
def test_failure_is_explicit_not_an_empty_scientific_result(peer, status, code):  # noqa: F811
    server, _, _ = peer
    selected, _, _ = inputs()
    server.status, server.body = status, b"SECRET"
    result = ResearchViewReader(ResearchViewTransport(f"http://127.0.0.1:{server.server_port}", "t" * 32)).read(selected)
    assert result.page is None and result.failure == "research_" + code
    assert result.calls == len(server.calls) == 1


def test_invalid_response_does_not_poison_next_independent_read(peer):  # noqa: F811
    server, _, _ = peer
    selected, raw, _ = inputs()
    reader = ResearchViewReader(ResearchViewTransport(f"http://127.0.0.1:{server.server_port}", "t" * 32))
    window = ResearchViewWindow()
    server.body = b"{}"
    assert reader.read(selected, window).page is None
    raw["query_sha256"] = "f" * 64
    server.body = json.dumps(raw).encode()
    assert reader.read(selected, window).failure == "research_view_invalid"
    raw["query_sha256"] = selected.query_sha256
    server.body = json.dumps(raw).encode()
    assert reader.read(selected, window).page is not None
    assert window.calls == 3


def test_closed_routes_and_owner_boundary():
    from amphora_agent_planning.peer_reads.profile import ReadProfile
    from amphora_agent_planning.research_view_access.transport import PROFILE
    with pytest.raises(ValueError, match="peer_read_route"):
        ReadProfile("knowledge", 20, 32, 4194304, dict(PROFILE.routes))
    with pytest.raises(ValueError, match="peer_read_route"):
        ReadProfile("research", 20, 32, 4194304, {"/v1/research-explore/sql": next(iter(PROFILE.routes.values()))})


def test_actual_catalog_http_and_series_has_no_implied_experiment(peer):  # noqa: F811
    server, _, _ = peer
    selected, _, data = inputs()
    server.body = json.dumps(data["catalog"]).encode()
    reader = ResearchViewReader(ResearchViewTransport(f"http://127.0.0.1:{server.server_port}", "t" * 32))
    assert reader.catalog(selected).experiment == selected.document().experiment
    assert server.calls[0][0] == "/v1/research-explore/catalog"
    with pytest.raises(ValueError, match="research_view_catalog_experiment"):
        reader.catalog(inputs("observation_series")[0])


def test_programming_error_is_not_reported_as_absent_science():
    class Broken:
        def read(self, *_args):
            raise ValueError("implementation_bug")
    with pytest.raises(ValueError, match="implementation_bug"):
        ResearchViewReader(Broken()).read(inputs()[0])


@pytest.mark.parametrize("budget,code", [("calls", "read_call_limit"), ("bytes", "read_byte_limit"),
                                        ("deadline", "read_expired")])
def test_shared_window_enforces_budget_before_accepting_result(peer, budget, code):  # noqa: F811
    server, _, _ = peer
    selected, raw, _ = inputs()
    server.body = json.dumps(raw).encode()
    reader = ResearchViewReader(ResearchViewTransport(f"http://127.0.0.1:{server.server_port}", "t" * 32))
    window = ResearchViewWindow()
    if budget == "calls":
        window.calls = 32
    elif budget == "bytes":
        window.consumed = 4194304
    else:
        window.deadline = 0
    result = reader.read(selected, window)
    assert result.page is None and result.failure == "research_" + code
    assert len(server.calls) == (1 if budget == "bytes" else 0)


def test_changed_limit_or_order_changes_query_and_position_cannot_cross_queries():
    selected, _, _ = inputs("properties")
    query = selected.document()
    other = query.observations[0].model_copy(update={"observation_id": "second"})
    first = ViewSelection.bind(query.model_copy(update={"observations": (*query.observations, other)}), selected.request)
    second = ViewSelection.bind(query.model_copy(update={"observations": (other, *query.observations)}), selected.request)
    assert first.query_sha256 != second.query_sha256
    assert ViewSelection.bind(query.model_copy(update={"limit": 1}), selected.request).query_sha256 != selected.query_sha256


def test_series_repeated_coordinates_and_quality_survive_without_numeric_coercion():
    selected, raw, _ = inputs("observation_series")
    selected = ViewSelection.bind(selected.document().model_copy(update={"limit": 2}), selected.request)
    raw.update(request=selected.document().model_dump(mode="json"), query_sha256=selected.query_sha256, next_position=None)
    raw["points"].append(copy.deepcopy(raw["points"][0]))
    page = ViewPage.bind(selected, page_model(selected, raw)).document()
    assert page.points[0] == page.points[1]
    assert page.model_dump(mode="json")["quality"] == raw["quality"]


def test_full_request_echo_is_bound_even_with_correct_digest():
    selected, raw, _ = inputs()
    raw["request"]["experiment"]["revision"] += 1
    with pytest.raises(ValueError, match="research_view_identity"):
        ViewPage.bind(selected, page_model(selected, raw))


def test_wrong_profile_and_forged_wire_values_are_rejected():
    from amphora_agent_planning.campaign_research_access import CampaignResearchWindow
    selected, raw, _ = inputs()
    with pytest.raises(ValueError, match="research_view_profile"):
        ResearchViewReader(None).read(selected, CampaignResearchWindow())
    with pytest.raises(ValueError, match="research_view_profile"):
        ResearchViewReader(None).catalog(selected, CampaignResearchWindow())
    with pytest.raises(ValueError, match="research_view_response_type"):
        ViewPage.bind(selected, selected.document())
    with pytest.raises(ValueError):
        ViewPage.bind(selected, page_model(selected, raw).model_copy(update={"total": True}))
