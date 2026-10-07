"""Explicit synthetic correction evidence; no resume, mutation or admission grant."""

import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from amphora_contracts_core import ArtifactRef
from amphora_contracts_search import SearchSpec, search_spec_schema

spec = importlib.util.spec_from_file_location("correction_manifest", Path(__file__).with_name("manifest.py"))
M = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = M
spec.loader.exec_module(M)


@dataclass(frozen=True)
class CorrectionRevision:
    previous: M.CheckpointEvidence
    specification_artifact: ArtifactRef
    specification: SearchSpec

    @classmethod
    def prepare(cls, previous, artifact, payload):
        ref = ArtifactRef.model_validate_json(M.canonical(artifact))
        new = SearchSpec.model_validate_json(payload)
        M.require(ref.schema_ref == search_spec_schema(), "correction_specification_schema")
        M.require(ref.sha256 == hashlib.sha256(payload).hexdigest() and ref.size_bytes == len(payload), "correction_specification_bytes")
        M.require(M.canonical(new.model_dump(mode="json")) == payload, "correction_specification_canonical")
        old = previous.checkpoint.specification
        M.require(new.scope == old.scope == ref.scope, "correction_scope")
        M.require(previous.checkpoint.phase in {"selected", "stopped"} and previous.checkpoint.selection is not None, "correction_original_rank_missing")
        M.require(new.search_id != old.search_id, "correction_revision_identity")
        M.require(new.evaluator.tool != old.evaluator.tool, "correction_evaluator_unchanged")
        M.require(new.evaluator.tool.capability_id == old.evaluator.tool.capability_id and
                  new.evaluator.tool.contract_version == old.evaluator.tool.contract_version, "correction_evaluator_contract")
        before, after = old.model_dump(mode="json"), new.model_dump(mode="json")
        for value in (before, after):
            del value["search_id"]
            del value["evaluator"]["tool"]
        M.require(before == after, "correction_unrelated_specification_change")
        return cls(previous, ref, new)

    def record(self):
        old = self.previous.checkpoint
        return {"profile": "search-correction-evidence-v1", "mode": "new_search_from_declared_seed", "resume": False,
                "authority": "synthetic_engineering_evidence_only", "prior": {
                    "checkpoint": self.previous.artifact.model_dump(mode="json"), "specification_sha256": old.specification_sha256,
                    "selection_sha256": hashlib.sha256(M.canonical(old.selection.model_dump(mode="json"))).hexdigest(),
                    "evaluator": old.specification.evaluator.tool.model_dump(mode="json")},
                "next": {"specification": self.specification_artifact.model_dump(mode="json"),
                         "specification_sha256": hashlib.sha256(M.canonical(self.specification.model_dump(mode="json"))).hexdigest(),
                         "evaluator": self.specification.evaluator.tool.model_dump(mode="json")},
                "fitness_reuse": "forbidden_evaluator_revision_changed", "scientific_improvement": "not_established"}
