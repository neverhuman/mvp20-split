"""Retained plans restore independently of mutable host catalogs and reject mismatched evidence."""

import json
from copy import deepcopy

import pytest
from amphora_campaign_runtime.definitions.material import ValidationMaterial, VerifiedDraftPlan
from amphora_campaign_runtime.definitions.revisions import DraftVersion
from amphora_campaign_runtime.definitions.validation import ValidationUniverse
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_core import Scope
from amphora_contracts_graph_runtime import AdmitDraft, DraftValidation, SaveDraft

from .test_commands import command
from .test_revisions import save
from .test_validate import request, setup


def test_restored_plan_is_pinned_despite_later_draft_head(fixture_env):
    e = fixture_env
    saves, validator, _ = setup(e)
    receipt = validator.validate(e.principal, request(e))
    saves.save(e.principal, command(e, "new-head", 1, "Another title"))
    repository = ValidationMaterial(e.engine)
    retained = repository.load(e.principal.scope, receipt.outcome.committed.object_id)
    assert retained.draft.revision == 1 and retained.entry.plan.sha256 == retained.validation.plan_sha256
    assert retained.entry.scope == e.principal.scope
    # Reconstructing the repository has no configured-plan or discovery dependency.
    replaced = ValidationMaterial(e.engine).load(e.principal.scope, receipt.outcome.committed.object_id)
    assert replaced.entry.plan == retained.entry.plan and replaced.validation == retained.validation
    with pytest.raises(TransitionError, match="graph_validation_unavailable"):
        repository.load(Scope(tenant_id="foreign", project_id="foreign"), receipt.outcome.committed.object_id)


def test_restoration_rejects_changed_plan_and_cross_revision_evidence():
    draft = DraftVersion.save(save(), None)
    universe = ValidationUniverse(draft.content.definition.scope, (), ())
    validation = universe.validate(draft).to_wire("validation")
    altered = json.loads(validation.model_dump_json())
    altered["plan_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="compilation_mismatch"):
        VerifiedDraftPlan.restore(draft, DraftValidation.model_validate_json(json.dumps(altered)), universe.record())
    next_draft = DraftVersion.save(save(1, "Next"), draft)
    with pytest.raises(ValueError, match="draft_identity_mismatch"):
        VerifiedDraftPlan.restore(next_draft, validation, universe.record())
    altered.update(structurally_valid=False, plan_sha256=None)
    with pytest.raises(TransitionError, match="not_structurally_valid"):
        VerifiedDraftPlan.restore(draft, DraftValidation.model_validate_json(json.dumps(altered)), universe.record())


def test_tool_plan_restores_exact_descriptors_and_schema_bytes(compiler_env):
    raw = deepcopy(compiler_env.raw[0])
    raw.update(schema_version="4", profile="deterministic-v3")
    draft = DraftVersion.save(SaveDraft.model_validate_json(json.dumps({"draft_id": "tool-draft", "expected_revision": 0,
        "title": "Tool plan", "definition": raw})), None)
    universe = ValidationUniverse(draft.content.definition.scope, (compiler_env.tool,), tuple(compiler_env.schema_list))
    outcome = universe.validate(draft)
    assert outcome.entry is not None
    retained = VerifiedDraftPlan.restore(draft, outcome.to_wire("tool-validation"), universe.record())
    assert retained.entry.plan == outcome.entry.plan
    assert retained.entry.descriptor(compiler_env.tool.lock.tool) == compiler_env.tool.descriptor.tool
    assert tuple(s.source_bytes for s in retained.universe.schemas) == tuple(s.source_bytes for s in compiler_env.schema_list)


def test_admission_selection_cannot_mix_validation_pins():
    draft = DraftVersion.save(save(), None)
    universe = ValidationUniverse(draft.content.definition.scope, (), ())
    validation = universe.validate(draft).to_wire("validation")
    retained = VerifiedDraftPlan.restore(draft, validation, universe.record())
    raw = {"plan_sha256": validation.plan_sha256, "inputs": [], "budget": {"limit": 1}, "draft": {
        "draft_id": draft.draft_id, "revision": draft.revision, "content_sha256": draft.content.sha256,
        "validation_id": validation.validation_id, "universe_sha256": universe.sha256}}
    assert retained.require_selection(AdmitDraft.model_validate_json(json.dumps(raw))) is retained.entry
    for key, wrong in (("draft_id", "other"), ("revision", 2), ("content_sha256", "0" * 64),
                       ("validation_id", "other"), ("universe_sha256", "0" * 64), ("plan_sha256", "0" * 64)):
        changed = deepcopy(raw)
        (changed if key == "plan_sha256" else changed["draft"])[key] = wrong
        with pytest.raises(TransitionError, match="selection_mismatch"):
            retained.require_selection(AdmitDraft.model_validate_json(json.dumps(changed)))
