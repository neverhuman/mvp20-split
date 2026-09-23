#!/usr/bin/env python3
"""DSSE-Ed25519-sign the DR-RUBRIC campaign-item done receipt for
amphora-dataset-recon. AUDIT_ONLY. Pinned Phase-0 evaluator key only.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
ITEM = MOD / "evidence/phase0/repairs/DR-RUBRIC"
WORK = ITEM / "work"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"

FIRE_ID = "20260810T040001-863993-9a3373941084"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


directive_bytes = DIRECTIVE_MD.read_bytes()
directive_sha_actual = sha(directive_bytes)
assert directive_sha_actual == DIRECTIVE_SHA_EXPECTED, "directive md sha mismatch: %s" % directive_sha_actual

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

diagnostic = json.loads((WORK / "diagnostic.canonical.json").read_bytes())
assert diagnostic["claim_verdict"] == "CLAIM_SURVIVED"
assert diagnostic["refutation_criterion_observed"] is False

# self-verify the two-replay + positive-control + independent-check facts straight
# from the on-disk artifacts, independent of what run_all.py already asserted
runA_sha = sha((WORK / "runA.json").read_bytes())
runB_sha = sha((WORK / "runB.json").read_bytes())
assert runA_sha == runB_sha == diagnostic["step1_real_two_replay"]["runA_sha256"]
runA_defect_sha = sha((WORK / "runA_defect.json").read_bytes())
runB_defect_sha = sha((WORK / "runB_defect.json").read_bytes())
assert runA_defect_sha != runB_defect_sha, "positive control did not fire on re-verification"
runC_sha = sha((WORK / "runC_independent.json").read_bytes())
assert runC_sha == runA_sha, "independent second-party check does not match scorer.py on re-verification"

rubric_sha = sha((WORK / "rubric.v1.json").read_bytes())
snapshot_sha = sha((WORK / "candidate_snapshot.v1.json").read_bytes())
mutated_snapshot_sha = sha((WORK / "candidate_snapshot_mutated_c1_rights.v1.json").read_bytes())
scorer_sha = sha((WORK / "scorer.py").read_bytes())
independent_check_sha = sha((WORK / "independent_reference_check.py").read_bytes())

body_obj = {
    "schema": "amphora.dataset-recon.repair-done.dr-rubric.v1",
    "module": "amphora-dataset-recon",
    "campaign_item_id": "DR-RUBRIC",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "fire_id": FIRE_ID,
    "date": "2026-08-10",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "no_acquisition_attestation": (
        "This fire performed zero new web queries, fetches, downloads, or acquisition. "
        "The frozen candidate snapshot's four candidates (C1-C4) are built entirely from "
        "facts already surfaced and recorded by the prior PROBE-WEB fire "
        "(search-record.v1.jsonl line 1, sha256 "
        "0fd12053ad9db240c027485f01ef3c4a625291da6f2b1639ee55592419f8f651, and the "
        "PROBE-WEB done receipt). Nothing landed on xbabe2 this fire except pure-Python "
        "JSON computation over already-authored fixture files under this item's work/ "
        "directory, and this receipt. No dataset ledger line was appended this fire "
        "(this item's deliverable is the rubric and its determinism proof, not a "
        "disposition-ledger entry -- the frozen snapshot is explicitly labeled as a "
        "rubric-testing fixture, not a ledger entry, in its own 'purpose' field)."
    ),
    "done_criterion_verbatim": (
        "Signed rubric artifact covering at least the six mandated dimensions (gap fit, "
        "provenance & measurement quality, rights clarity, uniqueness, integrity risk, "
        "acquisition cost & friction), each with a scoring rule a second party could "
        "apply; byte-stable two-replay of the ranking over a frozen candidate snapshot."
    ),
    "done_criterion_met": True,
    "claim_tested": (
        "The current DR-RUBRIC deliverable state is complete and accurate for its scope "
        "(finding a miss is CLAIM_REFUTED and is progress)."
    ),
    "claim_verdict": diagnostic["claim_verdict"],
    "attack_shape_executed": (
        "Re-ran the published rubric over the same frozen snapshot and attacked "
        "determinism (step1 + positive control in step2); then re-implemented the "
        "rubric independently from its own published tables, never importing the "
        "reference scorer, to attack second-party-applicability (step3); then mutated "
        "one scored attribute (candidate C1's rights_tier, an agreement-gated license "
        "flipped to quarantined/prohibited) in a snapshot copy and attacked whether the "
        "rank/verdict move exactly as the rubric's own published formula predicts (step4)."
    ),
    "directive_path": "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md",
    "directive_sha256": directive_sha_actual,
    "directive_obligation": "DR-RUBRIC",
    "directive_refutation_criterion_verbatim": (
        "Re-running the published rubric over the same frozen candidate snapshot yields "
        "a different ranking or verdict for any candidate, or any of the six mandated "
        "dimensions has no scoring rule a second party could apply."
    ),
    "directive_refutation_criterion_observation": (
        "DID NOT OCCUR. Two independent invocations of scorer.py over the byte-identical "
        f"frozen snapshot produced SHA-256-identical output ({runA_sha}) -- no candidate's "
        "ranking or verdict differed across the replay. All six mandated dimensions "
        "(gap_fit, provenance_measurement_quality, rights_clarity, uniqueness, "
        "integrity_risk, acquisition_cost_friction) are defined in rubric.v1.json as "
        "closed-vocabulary table lookups or fixed-formula sums of table lookups; "
        "independent_reference_check.py, a from-scratch re-implementation that never "
        f"imports scorer.py, reproduced byte-identical output (sha256 {runC_sha}), "
        "which is the operational proof that a second party applying only the published "
        "document reaches the same numbers. Verdict: CLAIM_SURVIVED, per the "
        "pre-committed criterion."
    ),
    "six_dimensions_present": [
        "gap_fit", "provenance_measurement_quality", "rights_clarity", "uniqueness",
        "integrity_risk", "acquisition_cost_friction",
    ],
    "positive_control": {
        "planted_defect": diagnostic["step2_positive_control_defect_planted_scorer"]["planted_defect"],
        "how_planted": diagnostic["step2_positive_control_defect_planted_scorer"]["how_planted"],
        "detected": diagnostic["step2_positive_control_defect_planted_scorer"]["detected"],
        "evidence": diagnostic["step2_positive_control_defect_planted_scorer"]["evidence"],
    },
    "mutation_sensitivity_attack": diagnostic["step4_mutation_sensitivity_attack"],
    "reproducibility": {
        "byte_identical": diagnostic["step1_real_two_replay"]["byte_identical"],
        "runA_sha256": diagnostic["step1_real_two_replay"]["runA_sha256"],
        "runB_sha256": diagnostic["step1_real_two_replay"]["runB_sha256"],
        "independent_second_party_sha256": runC_sha,
        "independent_second_party_matches_reference_scorer": (runC_sha == runA_sha),
        "replay_method": (
            "scorer.py was invoked twice as independent OS-level subprocess calls over "
            "the same frozen rubric.v1.json + candidate_snapshot.v1.json files; "
            "determinism is by construction (pure table lookups and fixed-point-rounded "
            "arithmetic, sort_keys=True canonical JSON, an explicit ascending-candidate-id "
            "tie-break rule, no wall-clock or random input). A defect-planted sibling "
            "script (scorer_nondeterministic.py) that adds a wall-clock field was run "
            "under the identical two-replay protocol and correctly failed to reproduce, "
            "confirming this is a real (non-vacuous) determinism gate."
        ),
    },
    "artifact_hashes": {
        "rubric.v1.json": rubric_sha,
        "candidate_snapshot.v1.json": snapshot_sha,
        "candidate_snapshot_mutated_c1_rights.v1.json": mutated_snapshot_sha,
        "scorer.py": scorer_sha,
        "independent_reference_check.py": independent_check_sha,
    },
    "artifact_paths": {
        "rubric": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/rubric.v1.json",
        "frozen_snapshot": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/candidate_snapshot.v1.json",
        "mutated_snapshot": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/candidate_snapshot_mutated_c1_rights.v1.json",
        "scorer": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/scorer.py",
        "independent_reference_check": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/independent_reference_check.py",
        "diagnostic": "amphora-dataset-recon/evidence/phase0/repairs/DR-RUBRIC/work/diagnostic.canonical.json",
    },
    "recon_mode_compliance": {
        "read_to_evaluate_only": True,
        "no_downloads_no_caching_no_scraping": True,
        "native_script_citations_preserved": (
            "candidate_snapshot.v1.json carries native_citation (native script) beside "
            "native_citation_romanization for every zh/ja candidate."
        ),
        "translation_confidence_rated_never_silently_accepted": (
            "Every candidate carries a translation_confidence field on the rubric's own "
            "closed vocabulary; C2's and C3's is honestly 'no_translation_attempted_unknown', "
            "not upgraded to look better than it is."
        ),
        "units_not_applicable_this_fire": "No physical measurement units are scored by this rubric artifact.",
        "credited_artifact_is_dsse_receipt": True,
        "ledger_lines_appended_this_fire": 0,
    },
    "does_not_close": [
        "No promotion, procurement, safety, synthesis, or freedom-to-operate authority.",
        "The frozen candidate snapshot is a rubric-testing fixture only -- none of its "
        "four candidates (C1-C4) were written to dataset-ledger.v1.jsonl or "
        "disposition-ledger.v1.jsonl this fire, and none should be treated as an actual "
        "portfolio recommendation until independently re-evaluated against fresh, "
        "directly-verified candidate facts (several of this fixture's fields, e.g. C1's "
        "rights_tier and C3/C4's data_class, are honestly marked 'unknown' or inferred "
        "from a single AI-tool summary, not a human-verified license read).",
        "Equal (1/6) dimension weighting is a disclosed design choice, not a directive "
        "mandate; a future rubric v2 may re-weight, but must do so as a published, "
        "re-tested revision, never a silent substitution.",
        "Does not modify or re-sign PROBE-WEB's done receipt or search-record.v1.jsonl; "
        "both are referenced by path + sha256 only.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/DR-RUBRIC/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.dataset-recon-repair-done-dr-rubric+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}
out = ITEM / "done" / "dr-rubric-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("claim_verdict", body_obj["claim_verdict"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
