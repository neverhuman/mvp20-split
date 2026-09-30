"""Independent draft revision and identity oracles; no persistence claim."""

import json

import pytest
from amphora_campaign_runtime.definitions.revisions import DraftConflict, DraftVersion
from amphora_contracts_graph_runtime import DraftRevision, SaveDraft


def save(revision=0, title="Research", **definition_changes):
    definition = {"schema_version": "4", "profile": "deterministic-v3", "campaign_id": "research", "revision": 1,
        "scope": {"tenant_id": "test", "project_id": "drafts"},
        "body": {"nodes": [{"kind": "finish", "node_id": "done", "outputs": []}]}, **definition_changes}
    return SaveDraft.model_validate_json(json.dumps({"draft_id": "draft", "expected_revision": revision,
        "title": title, "definition": definition}))


def test_stale_save_cannot_overwrite_or_mutate_prior_revision():
    first = DraftVersion.save(save(), None)
    second = DraftVersion.save(save(1, "Updated"), first)
    assert first.revision == 1 and first.content.title == "Research"
    assert second.revision == 2 and second.content.title == "Updated"
    assert first.content.sha256 != second.content.sha256
    with pytest.raises(DraftConflict, match="draft_revision_conflict"):
        DraftVersion.save(save(1, "Stale"), second)
    assert second.to_wire().parent_revision == 1
    assert DraftVersion.from_wire(second.to_wire()) == second


def test_identity_changes_require_a_new_draft():
    first = DraftVersion.save(save(), None)
    for changed in ({"campaign_id": "other"}, {"scope": {"tenant_id": "foreign", "project_id": "drafts"}}):
        with pytest.raises(DraftConflict, match="draft_identity_conflict"):
            DraftVersion.save(save(1, **changed), first)
    with pytest.raises(ValueError, match="draft_title_empty"):
        DraftVersion.save(save(title="   "), None)


def test_content_identity_detects_corruption_and_is_separate_from_revision():
    first = DraftVersion.save(save(), None)
    second = DraftVersion.save(save(1), first)
    assert first.content.sha256 == second.content.sha256
    corrupted = json.loads(first.to_wire().model_dump_json())
    corrupted["head"]["title"] = "Tampered"
    with pytest.raises(ValueError, match="draft_content_mismatch"):
        DraftVersion.from_wire(DraftRevision.model_validate_json(json.dumps(corrupted)))
