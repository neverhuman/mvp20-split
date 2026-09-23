#!/usr/bin/env python3
"""DSSE-Ed25519-sign the three-series-barrier-ranking-v1 AUDIT_ONLY receipt for
amphora-barrier-corrosion-score. AUDIT_ONLY: signs an audit receipt under the
module's benchmarks/ dir; does NOT sign a phase0 evaluation/review, does NOT
promote authority, does NOT flip scientific_readiness (stays UNVALIDATED /
PRE_PHASE_0), does NOT modify the portfolio manifest. It DOES leave
predictive_model_status / candidate_prediction_status as-is (FAILED) in
corrosion_series.json -- a separate, disclosed, non-manifest edit made by this
same fire and hash-recorded here for provenance, not performed by this script."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-barrier-corrosion-score/benchmarks/three-series-barrier-ranking-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
CORROSION_SERIES = ROOT / "amphora-barrier-corrosion-score/reference/mvp20/data/corrosion_series.json"


def sha(b): return hashlib.sha256(b).hexdigest()


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


script_bytes = (BENCH / "analyze_three_series_barrier_ranking.py").read_bytes()
script_sha256 = sha(script_bytes)


def replay_check():
    canon = (BENCH / "result.canonical.json").read_bytes()
    runA = (BENCH / "result.runA.json").read_bytes()
    runB = (BENCH / "result.runB.json").read_bytes()
    assert canon == runA == runB, "two-replay bytes differ"
    return sha(canon)


result_sha = replay_check()
result = json.loads((BENCH / "result.canonical.json").read_text())
corrosion_series_bytes_post_update = CORROSION_SERIES.read_bytes()

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
eval_pin = rev_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
    rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.barrier-corrosion-score.three-series-barrier-ranking-receipt.v1",
    "module": "amphora-barrier-corrosion-score",
    "benchmark": "three-series-barrier-ranking-v1",
    "campaign_item_id": "W1",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "opened_or_parsed_quarantined_asset": False,
    "quarantined_asset_touched": {
        "path": "amphora-barrier-corrosion-score/reference/eis/st-19168/raw/19168_inhibitive_coating_system_data.xlsx",
        "touched": False,
        "note": "ST-19168 remains rights-quarantined and untouched; this receipt analyzes only the 3 CC-BY literature series unlocked by campaign item C4.",
    },
    "purpose": (
        "FIRST-EVER execution of the mission.md-locked primary KPI test (blinded "
        "Kendall tau at metrics.barrier_index >= 0.50, superior to solids-only and "
        "PVC-only hostile nulls) against real, rights-clean, in-class, open-table-read "
        "data: the 3 CC-BY literature series (asperti2024, zhu2022, "
        "alam2022_pa450_pa3282 E-series) that campaign item C4 hash-locked to bring "
        "corrosion_series.json.strict_literature_count from 2 to 3, meeting the module's "
        "own >=3 literature bar. Adapts (with full disclosure, see script docstring) "
        "the frozen benchmarks/st19168-preregistered-v1/analyze_st19168_preregistered.py "
        "primitives and pre-committed constants (ALPHA=0.05, LOCKED_TAU_TARGET=0.50, "
        "FEASIBILITY_FLOOR=6) unchanged, to a per-series (no cross-study pooling) design "
        "honoring each source's declared use_limit."
    ),
    "adaptation_disclosure": {
        "frozen_script_path": "amphora-barrier-corrosion-score/benchmarks/st19168-preregistered-v1/analyze_st19168_preregistered.py",
        "frozen_script_sha256": result["provenance"]["frozen_st19168_preregistered_script_sha256"],
        "adapted_script_path": "amphora-barrier-corrosion-score/benchmarks/three-series-barrier-ranking-v1/analyze_three_series_barrier_ranking.py",
        "adapted_script_sha256": script_sha256,
        "deviation_disclosure_norm": "Nosek, Ebersole, DeHaven & Mellor 2018, PNAS 115(11):2600-2606",
        "what_changed_and_why": (
            "(1) Per-series (no pooling) evaluation of 3 independent literature ladders "
            "instead of one 10-system ST-19168 draw -- required because ST-19168 remains "
            "rights-quarantined and each source's use_limit forbids cross-study pooling. "
            "(2) load_systems() no longer assumes locked_barrier_index is a precomputed "
            "input column; this script instead checks mechanically whether it is "
            "computable at all for these series and reports the finding (it is not -- see "
            "locked_predictor_availability in the result). Neither change alters ALPHA, "
            "LOCKED_TAU_TARGET, FEASIBILITY_FLOOR, or the tau_b/exact-permutation math, "
            "and neither was chosen after seeing whether it would help or hurt the result "
            "-- both are structural consequences of the campaign item's own instructions "
            "(honor use_limit; no cross-study pooling) and of the module's actual "
            "codebase (barrier_index is unconditionally None), not free parameters."
        ),
    },
    "mechanical_finding_locked_predictor_unavailable": {
        "claim": "metrics.barrier_index (EisPredictionV1.barrier_index) is unconditionally None on every code path in the live implementation",
        "lib_rs_sha256": result["provenance"]["lib_rs_sha256"],
        "live_test_confirmation": (
            "cargo test -p amphora-barrier-corrosion-score re-run live this fire (before "
            "writing this script): 5/5 tests passed, including "
            "test_fit_keeps_endpoints_separate_and_summary_never_claims_circuit, which "
            "asserts prediction.barrier_index.is_none() on a real fitted-model "
            "prediction with both other endpoints (rust creep, wet adhesion) populated -- "
            "i.e. the model works and predicts, but never emits a barrier_index."
        ),
        "second_independent_reason": (
            "predict() additionally requires EisObservationV1.spectrum (multi-frequency "
            "real/imaginary impedance points), rights_receipt_sha256, and "
            "rights_eligible=true; none of asperti2024/zhu2022/alam2022's CC-BY table-reads "
            "captured per-frequency spectra or an instrument-level rights receipt -- only "
            "a single summary resistance metric per formulation level."
        ),
    },
    "hostile_null_definition_provenance": {
        "convention": "solids-only == PVC-only == monotone-in-loading-level within a single-resin ladder (barrier-null-char-v1 convention)",
        "barrier_null_char_v1_receipt_sha256": result["provenance"]["barrier_null_char_v1_receipt_sha256"],
        "exception": "alam2022 E-series is unpigmented (PVC=0 constant) -- PVC-only null reported UNDEFINED_DEGENERATE, not conflated with solids-only",
        "cross_check": (
            "Informational (non-gated) tau_b(solids_null,truth) for asperti2024 (0.0) and "
            "zhu2022 (0.4) exactly reproduce the sign and value of the independently-coded "
            "Spearman rho already reported in barrier-null-char-v1, a useful non-circularity "
            "cross-check between two differently-implemented rank statistics."
        ),
    },
    "result_summary": {
        "n_series_evaluated": result["aggregate"]["n_series_evaluated"],
        "n_series_feasibility_ok": result["aggregate"]["n_series_feasibility_ok"],
        "n_series_locked_predictor_available": result["aggregate"]["n_series_locked_predictor_available"],
        "locked_kpi_verdict": result["aggregate"]["locked_kpi_verdict"],
        "per_series": [
            {"series_id": r["series_id"], "n_systems": r["n_systems"],
             "feasibility": r["feasibility"], "verdict": r["verdict"]}
            for r in result["primary_3_series_no_pooling"]
        ],
        "bonus_series_not_one_of_the_3": {
            "series_id": result["bonus_within_study_corroboration_not_one_of_the_3"]["series_id"],
            "verdict": result["bonus_within_study_corroboration_not_one_of_the_3"]["verdict"],
        },
    },
    "honest_power_statement": result["honest_power_statement"],
    "verdict_on_claim": {
        "claim_tested": "docs/mission.md falsifiable hypothesis: a locked barrier ranking (metrics.barrier_index) can outperform solids-only and PVC-only hostile nulls (blinded Kendall tau >= 0.5)",
        "outcome": "CLAIM_REFUTED",
        "why_refuted_not_merely_underpowered": (
            "Two independent, decisive, mechanical findings, neither of which depends on "
            "how much data becomes available in the future: (1) metrics.barrier_index is "
            "architecturally never computed by the current implementation -- there is no "
            "code path that assigns it a value, confirmed by live test execution, not just "
            "static reading. The locked predictor does not exist, so the KPI cannot be "
            "evaluated even in principle against the current codebase. (2) Independently, "
            "even if a working predictor existed, all 3 currently available strict-in-class "
            "series (n=3,4,5) are below the pre-committed FEASIBILITY_FLOOR=6 from the "
            "frozen protocol, and the alam2022 E-series (n=3) is combinatorially incapable "
            "of ever reaching alpha=0.05 one-sided significance at any observed tau. "
            "Both are stronger and more decisive than an ordinary underpowered-null result."
        ),
        "predictive_model_status_action": "LEFT AS FAILED in corrosion_series.json -- the evidence supports no change; this receipt supplies the first real execution backing that status instead of an assertion.",
    },
    "corrosion_series_json_post_update_sha256": sha(corrosion_series_bytes_post_update),
    "result_canonical_sha256": result_sha,
    "two_replay_byte_stable": True,
    "does_not_close": [
        "No claim about ST-19168's real numeric content is made anywhere in this package; ST-19168 remains untouched and rights-quarantined.",
        "This receipt does not itself constitute the mission.md locked primary KPI (a "
        "blinded four-track independent-panel comparison); it is the first real-data "
        "execution of a smaller, honestly-scoped literature corroboration of the same "
        "statistical question.",
        "Promotes no authority, phase, or manifest state. predictive_model_status remains "
        "FAILED, exactly as before, now with concrete supporting evidence.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under amphora-barrier-corrosion-score/benchmarks/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.barrier-corrosion-three-series-barrier-ranking+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "three-series-barrier-ranking-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
# verify immediately
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("script_sha256", script_sha256)
print("result_sha256", result_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
