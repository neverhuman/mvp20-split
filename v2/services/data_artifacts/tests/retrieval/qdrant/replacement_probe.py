"""Fresh independently installed Data owner reconstructs retained generation and index."""

import importlib.metadata
import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from amphora_contracts_core import Scope
from amphora_data_artifacts.publication.model import Principal
from amphora_data_artifacts.reads import ArtifactReads
from amphora_data_artifacts.retrieval.identity import BuildAttempt
from amphora_data_artifacts.retrieval.intents import GenerationIntents
from amphora_data_artifacts.retrieval.leases import GenerationLease
from amphora_data_artifacts.retrieval.manifest import point_id
from amphora_data_artifacts.retrieval.mapping import reference_from_wire
from amphora_data_artifacts.retrieval.proof_records import head, verification
from amphora_data_artifacts.retrieval.publication import GenerationPublication
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.qdrant.configuration import QdrantConfiguration
from amphora_data_artifacts.retrieval.records import key_for, load_plan
from amphora_data_artifacts.storage.local import LocalBytes
from sqlalchemy import create_engine


def main():
    for module in ("amphora_research", "amphora_knowledge", "amphora_campaign_runtime"):
        assert importlib.util.find_spec(module) is None, "Isolated Data owner interpreter required"
    handoff = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    engine = create_engine(os.environ["AMPHORA_REPLACEMENT_DATABASE_URL"])
    principal = Principal(
        handoff["actor_id"], Scope.model_validate(handoff["scope"]), frozenset(handoff["actions"])
    )
    adapter = QdrantAdapter(
        QdrantConfiguration(handoff["endpoint"], os.environ["AMPHORA_REPLACEMENT_API_KEY"])
    )
    reads = ArtifactReads(engine, LocalBytes(Path(handoff["storage"])), 65536)
    intents = GenerationIntents(engine, adapter.reference)
    status = intents.read(principal, handoff["corpus_id"], handoff["generation_id"])
    with engine.connect() as connection:
        plan = load_plan(connection, principal, handoff["corpus_id"], handoff["generation_id"])
        proof = verification(connection, key_for(principal, plan.corpus_id, plan.generation_id), plan)
        selected = head(connection, principal, plan.corpus_id)
    reference = reference_from_wire(status.generation.reference)
    lease = GenerationLease(
        BuildAttempt(reference, handoff["token"], handoff["fence"]),
        datetime.fromisoformat(handoff["expires_at"]),
    )
    assert GenerationPublication(reads, adapter).publish(principal, lease) == status
    points = tuple(point_id(binding) for binding in status.generation.manifest.bindings)
    scored = adapter.query(proof.attempt.namespace, (0.0, 2.0, 2.0) + (0.0,) * 13, points)
    output = {
        "pid": os.getpid(),
        "package": importlib.metadata.version("amphora-data-artifacts"),
        "status": status.model_dump(mode="json"),
        "selected": selected.descriptor(),
        "namespace": proof.attempt.namespace,
        "projection_sha256": proof.projection_sha256,
        "scores": sorted(point.score for point in scored),
    }
    engine.dispose()
    print(json.dumps(output, separators=(",", ":")))


if __name__ == "__main__":
    main()
