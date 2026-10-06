"""Load exact frozen engineering bytes; no credentials, networking or generation."""

import hashlib
import json
from pathlib import Path

from amphora_agent_planning.access import Principal
from amphora_agent_planning.evaluation_batch.storage import EvaluationJournal
from amphora_agent_planning.openai_provider import OpenAIProvider
from amphora_agent_planning.openai_provider.evaluation import FrozenOpenAIEvaluation
from amphora_contracts_core import Scope

ROOT = Path(__file__).absolute().parents[1] / "dev/evaluation_corpora/openai-engineering-v1"


def load_bundle(transport, root=ROOT):
    inputs = json.loads((root / "inputs.json").read_bytes())
    original = next(iter(inputs.values()))["request"]
    principal = Principal(
        original["actor_id"],
        Scope.model_validate(original["reference"]["scope"]),
        frozenset({"record_requests", "record_attempts", "read_attempts"}),
    )
    protocol, batch = EvaluationJournal._decode(
        principal,
        (root / "manifest.json").read_bytes(),
        (root / "corpus.json").read_bytes(),
        (root / "inputs.json").read_bytes(),
    )
    bodies = json.loads((root / "bodies.json").read_bytes())
    provider = OpenAIProvider(transport, lambda ref: bodies[ref.sha256].encode("utf-8"), revision=protocol.manifest.adapter_revision)
    frozen = FrozenOpenAIEvaluation(protocol, batch, provider)
    expected = json.loads((root / "freeze.json").read_bytes())
    assert expected["protocol_sha256"] == protocol.sha256 and expected["batch_sha256"] == batch.sha256
    assert expected["packets"] == {
        key: hashlib.sha256(value.body).hexdigest() for key, value in frozen.prepared.items()
    }
    return principal, protocol, batch, frozen
