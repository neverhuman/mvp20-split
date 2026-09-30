"""Pinned pure validation outcomes and retained exact compiler material."""

import copy
import json

import pytest
from amphora_campaign_runtime.definitions.revisions import DraftVersion
from amphora_campaign_runtime.definitions.validation import ValidationUniverse
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import SaveDraft

from .test_revisions import save


def test_validation_never_grants_execution_or_scientific_acceptance():
    draft = DraftVersion.save(save(), None)
    universe = ValidationUniverse(draft.content.definition.scope, (), ())
    result = universe.validate(draft).to_wire("validation-1")
    assert result.structurally_valid and result.plan_sha256
    assert result.content_sha256 == draft.content.sha256 and result.revision == 1
    assert result.scientific_acceptance == "not_established"
    assert {"activation", "current_eligibility", "scientific_applicability"} <= set(result.pending_checks)
    bad = json.loads(save().model_dump_json())
    bad["definition"]["body"]["nodes"].append({"kind": "finish", "node_id": "second", "outputs": []})
    invalid = DraftVersion.save(SaveDraft.model_validate_json(json.dumps(bad)), None)
    failed = universe.validate(invalid).to_wire("validation-2")
    assert not failed.structurally_valid and failed.plan_sha256 is None and failed.findings


def test_universe_identity_is_order_independent_scoped_and_restorable(compiler_env):
    scope = Scope(tenant_id="test", project_id="drafts")
    universe = ValidationUniverse(scope, (compiler_env.tool,), tuple(compiler_env.schema_list))
    reordered = ValidationUniverse(scope, (compiler_env.tool,), tuple(reversed(compiler_env.schema_list)))
    assert reordered.sha256 == universe.sha256
    assert ValidationUniverse.restore(universe.record(), universe.sha256).record() == universe.record()
    other = ValidationUniverse(Scope(tenant_id="other", project_id="drafts"), (), ())
    with pytest.raises(ValueError, match="scope_mismatch"):
        other.validate(DraftVersion.save(save(), None))
    corrupted = copy.deepcopy(universe.record())
    corrupted["schemas"][0]["bytes"] = "e30="
    with pytest.raises(ValueError, match="schema_digest_mismatch"):
        ValidationUniverse.restore(corrupted, universe.sha256)
    with pytest.raises(ValueError, match="digest_mismatch"):
        ValidationUniverse.restore(universe.record(), "0" * 64)


def test_universe_freezes_inputs_and_rejects_unbounded_restore(compiler_env):
    scope = Scope(tenant_id="test", project_id="drafts")
    tools, schemas = [compiler_env.tool], list(compiler_env.schema_list)
    universe = ValidationUniverse(scope, tools, schemas)
    digest = universe.sha256
    tools.clear()
    schemas.clear()
    assert universe.sha256 == digest and len(universe.releases) == 1
    record = universe.record()
    record["schemas"][0]["bytes"] = "a" * 87385
    with pytest.raises(ValueError, match="invalid_retained_schema"):
        ValidationUniverse.restore(record, digest)
    record = universe.record()
    record["tools"] *= 65
    with pytest.raises(ValueError, match="authoring_universe_bound"):
        ValidationUniverse.restore(record, digest)


def test_universe_uses_only_materials_from_same_scope(compiler_env):
    from types import SimpleNamespace

    from amphora_campaign_runtime.definitions.universes import from_graphs
    first = Scope(tenant_id="test", project_id="drafts")
    second = Scope(tenant_id="other", project_id="drafts")
    reviewed = (SimpleNamespace(scope=first), (compiler_env.tool,), tuple(compiler_env.schema_list))
    universes = from_graphs((reviewed, reviewed, (SimpleNamespace(scope=second), (), ())))
    assert len(universes[("test", "drafts")].releases) == 1
    assert not universes[("other", "drafts")].releases
    with pytest.raises(TypeError):
        universes[("test", "drafts")] = None
