"""Synthetic public-client doubles; no owner acceptance claim."""

import hashlib
from types import SimpleNamespace

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import candidate_birth_schema, population_specification_schema
from amphora_evolution_search.population import OriginalPopulation, canonical
from amphora_evolution_search.population_workers.artifacts import PopulationArtifacts

from ..population.conftest import population_original


class Attempt:
    def __init__(self):
        self.invocation = SimpleNamespace(attempt_id="attempt-1", run_id="admitted-run", inputs=(), checkpoint=None)
        self.live, self.refreshes = True, 0

    def check(self):
        if not self.live:
            from amphora_tool_protocol import ProtocolError
            raise ProtocolError("attempt_authority_lost")

    def refresh(self):
        self.check()
        self.refreshes += 1


class Client:
    def __init__(self, scope):
        self.identity = SimpleNamespace(scope=scope)
        self.uploads, self.contents, self.parents, self.calls = {}, {}, {}, []
        self.stream_failure = False

    def read(self, reference):
        return self.contents[reference.artifact_id]

    def begin_derived(self, content, declaration, command_id, *, guard):
        guard()
        self.calls.append(("begin", command_id))
        upload = SimpleNamespace(upload_id=command_id, content=content)
        self.uploads[command_id] = upload, declaration
        return SimpleNamespace(upload=upload)

    def stream(self, upload, raw, *, guard):
        guard()
        self.calls.append(("stream", upload.upload_id))
        if self.stream_failure:
            from amphora_tool_protocol import ProtocolError
            raise ProtocolError("stream_interrupted")
        self.contents[upload.upload_id] = raw

    def finalize(self, upload, command_id, *, guard):
        guard()
        self.calls.append(("finalize", command_id))
        artifact = ArtifactRef(artifact_id=upload.upload_id, scope=self.identity.scope,
            **upload.content.model_dump())
        self.parents[artifact.artifact_id] = self.uploads[upload.upload_id][1].inputs
        return SimpleNamespace(artifact=artifact)


@pytest.fixture
def worker_artifacts(population_original):
    original = OriginalPopulation(population_original.record.model_copy(update={"representation": candidate_birth_schema()}))
    client, attempt = Client(original.record.scope), Attempt()
    source = canonical(original.record)
    reference = ArtifactRef(artifact_id="original-spec", scope=original.record.scope,
        sha256=hashlib.sha256(source).hexdigest(), size_bytes=len(source), media_type="application/json",
        schema_ref=population_specification_schema())
    client.contents[reference.artifact_id] = source
    session = PopulationArtifacts(client, attempt, original.record.implementations[0])
    return SimpleNamespace(original=original, client=client, attempt=attempt, session=session, source=reference)
