import json
from hashlib import sha256
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_search import SearchSpec, search_checkpoint_schema
from amphora_contracts_search_steps import SearchStepContext
from amphora_evolution_search import BoundCheckpoint, InitialPopulation, OriginalSearch


@pytest.fixture
def context():
    original = OriginalSearch(SearchSpec.model_validate_json(
        (Path(__file__).parents[1] / "specification/synthetic_specification.json").read_bytes()))
    snapshot = InitialPopulation.generate(original).checkpoint()
    raw = snapshot.encode()
    reference = ArtifactRef(artifact_id="synthetic-checkpoint", scope=original.record.scope,
                            sha256=sha256(raw).hexdigest(), media_type="application/json",
                            schema_ref=search_checkpoint_schema(), size_bytes=len(raw))
    return SearchStepContext(original_specification=original.record, checkpoint=snapshot.record, checkpoint_artifact=reference)


def test_request_expansion_preserves_frozen_pending_identity(context):
    bound = BoundCheckpoint.from_context(context)
    batch = bound.request_batch()
    assert len(batch.requests) == 1
    assert batch.requests[0].evaluation_id == context.checkpoint.pending[0].evaluation_id
    assert batch.requests[0].candidate == context.checkpoint.attempts[0]
    assert batch.checkpoint_artifact == context.checkpoint_artifact


@pytest.mark.parametrize("field,value,code", [
    ("sha256", "f" * 64, "checkpoint_artifact_bytes"),
    ("size_bytes", 0, "checkpoint_artifact_bytes"),
    ("media_type", "text/plain", "checkpoint_artifact_schema"),
])
def test_mismatched_artifact_metadata(context, field, value, code):
    reference = context.checkpoint_artifact.model_copy(update={field: value})
    with pytest.raises(ValueError, match=code):
        BoundCheckpoint.from_context(context.model_copy(update={"checkpoint_artifact": reference}))


def test_schema_and_scope_pins_are_checked(context):
    scope = context.checkpoint_artifact.scope.model_copy(update={"project_id": "other"})
    reference = context.checkpoint_artifact.model_copy(update={"scope": scope})
    with pytest.raises(ValueError, match="checkpoint_artifact_scope"):
        BoundCheckpoint.from_context(context.model_copy(update={"checkpoint_artifact": reference}))
    schema = context.checkpoint_artifact.schema_ref.model_copy(update={"sha256": "f" * 64})
    reference = context.checkpoint_artifact.model_copy(update={"schema_ref": schema})
    with pytest.raises(ValueError, match="checkpoint_artifact_schema"):
        BoundCheckpoint.from_context(context.model_copy(update={"checkpoint_artifact": reference}))


def test_equivalent_but_noncanonical_source_bytes_are_not_falsely_verified(context):
    raw = json.dumps(context.checkpoint.model_dump(mode="json"), indent=2).encode()
    reference = context.checkpoint_artifact.model_copy(update={"sha256": sha256(raw).hexdigest(), "size_bytes": len(raw)})
    with pytest.raises(ValueError, match="checkpoint_artifact_bytes"):
        BoundCheckpoint.from_context(context.model_copy(update={"checkpoint_artifact": reference}))
