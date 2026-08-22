#!/usr/bin/env python3
"""Independent CPython oracle for the amphora-model-card-authority LIVE
runtime differential audit (live-runtime-envelope-parity-v1).

Predicts — from module-manifest.json plus the module's published
minimum-privilege specification (mission.md / capability-profile.json and the
two prior signed AUDIT_ONLY receipts) — the EXACT canonical-JSON bytes of the
score envelope the live native-Rust runtime must emit for the target module,
the exact display strings of the module-owned error taxonomy, and the
registry-identity facts. Zero Rust linkage; ground truth comes only from the
separately compiled probe binary (McKeeman 1998 differential testing).

Theory anchors:
- Saltzer & Schroeder 1975, "The Protection of Information in Computer
  Systems", Proc. IEEE 63(9), DOI 10.1109/PROC.1975.9939 — least privilege
  and fail-safe defaults: a mechanism that cannot prove authority must deny.
- McKeeman 1998, "Differential Testing for Software", Digital Technical
  Journal 10(1):100-107 — independent implementations compared on identical
  inputs expose divergence between specification and shipped behavior.
- Denning 1976 (lattice model, carried from the signed
  authority-lattice-completeness-v1 receipt): every grant is the meet of
  ceilings; no output may exceed the constraint tier.
"""
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = "amphora-model-card-authority"
MODULE_VERSION = "0.1.0-rust"

QUARANTINE_REASON = "Model cards do not authorize any scientific ranking objective."
CANDIDATE_TYPE_ERROR = "candidate type is not accepted by this capability"
FAIL_CLOSED_EXPLANATION = "Native capability failed closed."


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()


def load_manifest():
    manifest = json.loads((ROOT / "module-manifest.json").read_text())
    row = next(r for r in manifest["modules"] if r["project"] == MODULE)
    return manifest, row


def predicted_descriptor(row):
    """Registry identity: the live descriptor must be exactly the manifest
    row's least-privilege projection — nothing added, nothing widened."""
    return {
        "project": row["project"],
        "authority_ceiling": row["authority_ceiling"],
        "solver_use_ceiling": row["solver_use_ceiling"],
        "model_readiness_ceiling": row["model_readiness_ceiling"],
        "ranking_eligible": row["ranking_eligible"],
        "candidate_types": row["candidate_types"],
        "non_blocking_claim_locks": row["non_blocking_claim_locks"],
        "readiness": row["readiness"],
    }


def predicted_claim_locks(manifest, row):
    """Claim-lock union: module non-blocking locks plus every mandatory
    pre-Phase-0 policy lock, all pinned true (locked)."""
    locks = {}
    for lock in list(row["non_blocking_claim_locks"]) + list(
            manifest["policy"]["mandatory_claim_locks"]):
        locks[lock] = True
    return locks


def predicted_model_card(row):
    return {
        "model_id": f"{row['project']}.native-quarantine.v1",
        "model_authority": row["authority_ceiling"],
        "solver_use": row["solver_use_ceiling"],
        "model_readiness_status": row["model_readiness_ceiling"],
        "can_optimize": False,
        "current_pass": False,  # status is never SCORED for a model card
        "product_claim_ready": False,
        "scientific_applicability": "UNVALIDATED",
    }


def predicted_authority_receipt(row):
    return {
        "granted_level": row["model_readiness_ceiling"],
        "ranking_eligible": False,
        "registry_owned": True,
    }


def predicted_envelope(manifest, row, candidate_id, kind):
    """The full ScoreEnvelope the live runtime must emit.

    kind == "quarantined": in-domain candidate; the model card records
      authority but grants none — INSUFFICIENT_INPUT quarantine.
    kind == "candidate_type_error": out-of-domain candidate type; the
      capability fails closed with the exact taxonomy string.
    """
    metrics = {
        "authority_receipt": predicted_authority_receipt(row),
        "model_card": predicted_model_card(row),
        "model_readiness_status": row["model_readiness_ceiling"],
        "solver_use": row["solver_use_ceiling"],
    }
    if kind == "quarantined":
        status = "INSUFFICIENT_INPUT"
        semantics = "INSUFFICIENT_INPUT"
        missing = [QUARANTINE_REASON]
        explanations = [QUARANTINE_REASON]
        scope = "COMPUTATIONAL_DIAGNOSTIC_ONLY"
        metrics["ranking_quarantine"] = True
        metrics["scientific_applicability"] = "UNVALIDATED"
    elif kind == "candidate_type_error":
        status = "ERROR"
        semantics = "ERROR"
        missing = [CANDIDATE_TYPE_ERROR]
        explanations = [FAIL_CLOSED_EXPLANATION]
        scope = "NO_AUTHORITY"
    else:
        raise ValueError(kind)
    return {
        "module_id": row["project"],
        "module_version": MODULE_VERSION,
        "candidate_id": candidate_id,
        "status": status,
        "authority_tier": row["authority_ceiling"],
        "score_0_1": None,
        "objective_values": {},
        "metrics": metrics,
        "gates": {},
        "uncertainty": {},
        "claim_locks": predicted_claim_locks(manifest, row),
        "missing_inputs": missing,
        "explanations": explanations,
        "source_refs": [],
        "usable_by_optimizer": False,
        "evidence_scope": scope,
        "score_semantics": semantics,
        "schema_version": "amphora.score-envelope.v1",
    }


def predicted_error_taxonomy():
    """Exact Display bytes of the module-owned registry error taxonomy
    (thiserror #[error] formats published in the runtime source anchors)."""
    return {
        "resolve_unknown_module": "unknown native capability no-such-module",
        "report_unknown_lane":
            "native registry manifest is invalid: unknown lane no-such-lane",
        "unknown_campaign_module":
            "unknown native capability amphora-model-card-authorityx",
        "candidate_type_error": CANDIDATE_TYPE_ERROR,
    }


def predicted_registry_facts():
    """29 canonical modules; the target module must NOT be reachable from any
    default scoring lane (least privilege: only explicit campaign traversal
    reaches the authority registry surface)."""
    return {
        "module_count": 29,
        "report_schema": "amphora.module-manifest.v1",
        "implementation": "native-rust",
        "lane_active_contains_module": {
            "molecule": False,
            "formulation": False,
            "infrastructure": False,
        },
    }


def predictions():
    manifest, row = load_manifest()
    return {
        "descriptor": predicted_descriptor(row),
        "envelopes": {
            "F1_valid_formulation_seed0": predicted_envelope(
                manifest, row, "Envelope-65-black-canonical", "quarantined"),
            "F2_same_candidate_new_seed_new_runid": predicted_envelope(
                manifest, row, "Envelope-65-black-canonical", "quarantined"),
            "E1_evidence_package_wrong_type": predicted_envelope(
                manifest, row, "fixture-evidence-pass", "candidate_type_error"),
        },
        "errors": predicted_error_taxonomy(),
        "registry": predicted_registry_facts(),
    }


if __name__ == "__main__":
    print(json.dumps(predictions(), indent=1, sort_keys=True))
