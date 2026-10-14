import hashlib

import pytest
from amphora_contracts_core import ArtifactRef, SchemaRef, Scope
from amphora_contracts_population import GenerationIdentity, MaterialState, ProcessContext, population_record_schema
from amphora_process_mapping import PopulationArtifact, canonical


@pytest.fixture
def material_factory():
    scope = Scope(tenant_id="engineering", project_id="process")
    context = ProcessContext(generation=GenerationIdentity(scope=scope, run_id="process-run", specification_sha256="a" * 64,
        generation=0, predecessor=None), candidate_id="b" * 64, process_batch_id="experiment-1")
    schema = SchemaRef(schema_id="synthetic.material", version="1", sha256="c" * 64)
    def artifact(name, schema_ref, record=None):
        raw = canonical(record) if record is not None else b"{}"
        return PopulationArtifact(ArtifactRef(artifact_id=name, scope=scope, schema_ref=schema_ref,
            media_type="application/json", sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw)), raw)
    conditions = artifact("conditions", schema).reference
    def material(name, *, revision=1, current_context=context, state_id=None, current_conditions=conditions):
        record = MaterialState(schema_version="1", profile="synthetic-process-material-v1", context=current_context,
            state_id=state_id or name, revision=revision, kind="intermediate", representation=artifact("representation-" + name, schema).reference,
            composition=None, material_batch_id="batch-" + name, amount=None, phase=None, conditions=current_conditions,
            unknowns=("composition", "amount", "phase"))
        return artifact(name, population_record_schema("population.material-state"), record)
    return context, schema, conditions, artifact, material
