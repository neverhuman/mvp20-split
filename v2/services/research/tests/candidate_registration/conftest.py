import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_core import ArtifactRef, SchemaRef
from amphora_contracts_research import CandidateRevision
from amphora_research.candidate_registration.profiles import (
    CandidateProfile,
    CandidateProfiles,
    schema_reference,
)
from amphora_research.candidate_registration.registration import CandidateRegistrar
from amphora_research.transport.access import Principal


class MemoryReader:
    """Explicit peer fixture; cannot establish actual Data rights or HTTP."""

    def __init__(self, reference, body):
        self.reference, self.body, self.calls, self.error = reference, body, 0, None

    def read(self, reference):
        self.calls += 1
        assert reference == self.reference
        if self.error is not None:
            raise self.error
        return self.body


@pytest.fixture
def candidate_registration(ledger):
    store, scope = ledger
    data = json.loads(Path(__file__).with_name("sequence.json").read_bytes())
    data["scope"] = scope.model_dump(mode="json")
    raw = json.dumps(data).encode()
    reference = ArtifactRef(
        artifact_id="proposed-sequence",
        scope=scope,
        sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),
        media_type="application/json",
        schema_ref=schema_reference("candidate-space.sequence"),
    )
    profile = CandidateProfile(
        reference.schema_ref, "sequence", SchemaRef.model_validate(data["profile"])
    )
    reader = MemoryReader(reference, raw)
    registrar = CandidateRegistrar(
        store, CandidateProfiles([profile]), lambda supplied: reader
    )
    record = CandidateRevision.model_validate_json(
        json.dumps(
            {
                "wire_version": "1",
                "reference": {
                    "scope": scope.model_dump(mode="json"),
                    "candidate_id": "c",
                    "revision": 1,
                },
                "representation": reference.model_dump(mode="json"),
                "supersedes": None,
            }
        )
    )
    principal = Principal(
        "first", scope, frozenset({"declare_candidate", "read_candidate"})
    )
    return registrar, principal, record, reader
