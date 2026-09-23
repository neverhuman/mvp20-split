#!/usr/bin/env python3
"""Sign the V-A12a independent-verify done receipt with the PHASE0_EVALUATOR key."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-role-ranker/evidence/phase0/repairs/V-A12a"
WORK = OUT / "work"
DONE = OUT / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260804T090001-3198373-4c8699d8b0d7"
CAMPAIGN_ITEM_ID = "V-A12a"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


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


r_a12_done_path = OUT.parent / "R-A12/done/ra12_reinstatement_batch_receipt.v1.dsse.json"
r_a12_done_sha = sha_file(r_a12_done_path)

orig_probe_path = ROOT / "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/replay_receipt.v1.dsse.json"
orig_reactivity_path = ROOT / "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/replay_receipt.v1.dsse.json"
orig_probe_sha = sha_file(orig_probe_path)
orig_reactivity_sha = sha_file(orig_reactivity_path)

reactivity_script_path = ROOT / "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/run_reactivity_ratio.py"
reactivity_script_sha = sha_file(reactivity_script_path)
reactivity_canonical_path = ROOT / "amphora-molecule-role-ranker/benchmarks/role-reactivity-ratio-substitution-effect-v1/diagnostic.canonical.json"
reactivity_canonical_sha = sha_file(reactivity_canonical_path)

probe_canonical_path = ROOT / "amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1/diagnostic.canonical.json"
probe_canonical_sha = sha_file(probe_canonical_path)

escalation_runA = json.loads((WORK / "escalation_runA.json").read_text())
escalation_runB_sha = sha_file(WORK / "escalation_runB.json")
escalation_runA_sha = sha_file(WORK / "escalation_runA.json")
assert escalation_runA_sha == escalation_runB_sha, "escalation two-replay bytes differ"

verify_dsse_script_sha = sha_file(WORK / "va12a_verify_dsse.py")
escalation_script_sha = sha_file(WORK / "va12a_escalation_positive_r.py")

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert rev_pin, "reviewer key_id does not match pinned trust-store PHASE0_INTERNAL_REVIEWER entry"
assert eval_pub_hex == "6cf07abf1a55adaac13e78abc31c531d03d8f0d4232346344a736418c7b45664"

body_obj = {
    "schema": "amphora.molecule-role-ranker.v-a12a-independent-verify-receipt.v1",
    "receipt_id": "v-a12a-molecule-role-ranker-independent-verify-" + sha(r_a12_done_sha.encode())[:32],
    "fire_id": FIRE_ID,
    "campaign_item_id": CAMPAIGN_ITEM_ID,
    "repair_item_under_verify": "R-A12",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": True,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-molecule-role-ranker",
    "objective": (
        "INDEPENDENT VERIFY of interactive repair R-A12 (a DSSE signing-key "
        "reinstatement of 2 launcher-downgraded fires' falsification artifacts on "
        "amphora-molecule-role-ranker). This receipt's author did not write R-A12. "
        "Attacked claims: (1) the original defect on both reinstated artifacts is "
        "genuinely a wrong-signing-key problem (LOCAL_DEVELOPMENT_AUDIT_ONLY key, "
        "not malformed envelope, not fabricated science), not something R-A12 "
        "mischaracterized; (2) the anchored batch receipt genuinely verifies against "
        "the pinned PHASE0_EVALUATOR key; (3) the underlying science re-executes and "
        "reproduces; escalated past R-A12's own self-check with a fresh adjacent-"
        "stress probe and a fresh independent execution of the other artifact's "
        "already-built binary."
    ),
    "claim_under_attack": {
        "receipt": "amphora-molecule-role-ranker/evidence/phase0/repairs/R-A12/done/"
                   "ra12_reinstatement_batch_receipt.v1.dsse.json",
        "sha256": r_a12_done_sha,
        "text": "The interactive repair R-A12 withstands independent adversarial verification.",
    },
    "method": {
        "1_defect_reality_check": (
            "Independently rebuilt the DSSE PAE (\"DSSEv1\" SP len(type) SP type SP "
            "len(body) SP body) from first principles (fresh script, not reusing R-A12's "
            "own verifier) and Ed25519-verified both originally-reinstated artifacts "
            "against the PINNED PHASE0_EVALUATOR public key "
            "(6cf07abf1a55adaa...) AND against the repo LOCAL_DEVELOPMENT_AUDIT_ONLY "
            "public key (4b722f4516e0...)."),
        "2_reissue_verification": (
            "Ed25519-verified R-A12's own anchored batch receipt "
            "(ra12_reinstatement_batch_receipt.v1.dsse.json) against the pinned "
            "PHASE0_EVALUATOR key using the same from-scratch PAE reconstruction, and "
            "confirmed it does NOT verify against the local-dev key (proving it is "
            "genuinely signed by the trust-anchored key, not the unanchored one)."),
        "3_spot_rerun_reactivity_ratio": (
            "Re-executed the committed, UNMODIFIED run_reactivity_ratio.py "
            "(sha256-pinned before running) twice independently, confirmed both runs "
            "byte-identical to each other and to the committed diagnostic.canonical.json "
            "R-A12 cited."),
        "4_escalation_positive_substitution_stress": (
            "R-A12's reinstated reactivity-ratio benchmark only tested r=k2/k1 in "
            "{0.65,0.45} (Girard-Reydet et al. 1995, measured for AROMATIC diamines "
            "MDA/MDEA/MCDEA/DDS) applied to the benchmark's own ALIPHATIC eligible "
            "hardener set (IPDA/PACM/MXDA) -- a chemotype mismatch not flagged in the "
            "original does_not_close list. Aliphatic secondary amines are frequently "
            "MORE nucleophilic than primary (alkyl inductive effect increases "
            "basicity), i.e. a plausible r>1 positive-substitution regime for exactly "
            "the hardeners tested, which neither the original benchmark nor R-A12's "
            "self-check ever probed. Wrote a new script (imports the committed module's "
            "functions unmodified, verified by sha256 before import) that re-ran the "
            "same MC falsification criterion at r in "
            "{1/0.65=1.538 (positive mirror of the aromatic ratio), 1/0.45=2.222 "
            "(positive mirror of the extreme ratio), 3.0, 10.0} across all 3 eligible "
            "hardeners (12 tests), with FRESH seeds (salt \"escalate_v_a12a\", never used "
            "by the committed script's \"validate\"/\"attack\" salts), run twice for "
            "byte-stability."),
        "5_spot_rerun_live_runtime_probe": (
            "Executed R-A12's own already-compiled harness binary "
            "(role-live-runtime-domain-probe-harness, file mtime 2026-08-03T21:40:26Z, "
            "unchanged since R-A12's own reattack -- confirmed no rebuild occurred: my "
            "own cargo build attempts either failed at the C++ include-path step before "
            "I corrected it, or subsequently blocked and timed out on the advisory lock "
            "held by a concurrent agent's sccache process, per `flock -n .cron.lock` "
            "returning LOCK_HELD) five consecutive times in a fresh shell session; "
            "compared LD-linked RDKit .so provenance (ldd confirms linkage to the "
            "pinned rdkit-2026.03.2 prefix; those .so files' mtimes are 2026-07-18, "
            "unchanged) and diffed full JSON content (not just top-level hash) against "
            "both the committed diagnostic.canonical.json and R-A12's own stored "
            "probe_reattack_runA.json."),
    },
    "pre_registered_refute_criterion": (
        "CLAIM_REFUTED if: the original artifacts' signatures verify against the "
        "pinned evaluator key (defect not real); OR the reissued batch receipt fails "
        "to verify against the pinned key; OR the spot-rerun of the committed "
        "reactivity-ratio script disagrees with the committed diagnostic in any SCORED "
        "field; OR the escalation finds ANY (hardener, positive-r) combination where "
        "amine-starved sol is not strictly greater than amine-rich sol (H2 direction "
        "reversal); OR the live-runtime-probe rerun disagrees with the committed "
        "diagnostic in any SCORED probe (n_pass, n_disagreements, verdict, or any "
        "probe with scored=true)."
    ),
    "results": {
        "defect_reality": {
            "orig_probe_verifies_against_pinned_evaluator": False,
            "orig_probe_verifies_against_local_dev_key": True,
            "orig_probe_sha256": orig_probe_sha,
            "orig_reactivity_verifies_against_pinned_evaluator": False,
            "orig_reactivity_verifies_against_local_dev_key": True,
            "orig_reactivity_sha256": orig_reactivity_sha,
            "conclusion": (
                "CONFIRMED: both original artifacts are well-formed DSSE envelopes "
                "whose signatures cryptographically verify against the LOCAL_DEVELOPMENT_"
                "AUDIT_ONLY public key but fail against the pinned PHASE0_EVALUATOR key. "
                "R-A12's characterization of the original defect (wrong key, not "
                "malformed envelope, not fabricated science) is accurate."),
        },
        "reissue_verification": {
            "batch_receipt_verifies_against_pinned_evaluator": True,
            "batch_receipt_verifies_against_local_dev_key": False,
            "batch_receipt_sha256": r_a12_done_sha,
            "conclusion": "CONFIRMED: the anchored reissue is genuinely signed by the trust-anchored key.",
        },
        "spot_rerun_reactivity_ratio": {
            "committed_script_sha256": reactivity_script_sha,
            "committed_diagnostic_sha256": reactivity_canonical_sha,
            "my_rerun_runA_sha256": "1f5a95d058e775985b304e0f9c60cc4caa23f3f9133fc773353258adb5322b17",
            "my_rerun_runB_sha256": "1f5a95d058e775985b304e0f9c60cc4caa23f3f9133fc773353258adb5322b17",
            "byte_exact_match": True,
            "verdict_reproduced": "H2_SURVIVED_UNDER_LITERATURE_REACTIVITY_RATIO",
            "conclusion": "CONFIRMED: fully byte-exact independent reproduction, no caveats.",
        },
        "escalation_positive_substitution_stress": {
            "ratios_tested": escalation_runA["ratios_tested"],
            "eligible_hardeners": escalation_runA["eligible_hardeners"],
            "n_tests": escalation_runA["n_tests"],
            "n_reversals": escalation_runA["n_reversals"],
            "reversals": escalation_runA["reversals"],
            "two_replay_sha256": escalation_runA_sha,
            "verdict": escalation_runA["verdict"],
            "conclusion": (
                "H2 direction rule SURVIVED a genuinely novel, untested positive-"
                "substitution-effect regime (r up to 10.0) across all 3 eligible "
                "hardeners with fresh seeds: 0/12 reversals. This is a real escalation "
                "beyond R-A12's and the original benchmark's own scope (which only "
                "tested aromatic-diamine-derived negative ratios on aliphatic "
                "hardeners) and it did not break the claim."),
        },
        "spot_rerun_live_runtime_probe": {
            "committed_diagnostic_sha256": probe_canonical_sha,
            "r_a12_own_reattack_sha256": "9b03c2da5777e9578e8dadb1c32f4ab89e99af40546ba48d777d91f9bd6b7360",
            "my_rerun_sha256_5x_consecutive": "e0aa0f04ce0c8bb3cd1c494d6bbad869a1b704b72cac9d59d294c0338c2a35ff",
            "byte_exact_match_to_committed": False,
            "discrepancy_confined_to": "dicy-dicyandiamide probe only (the ONE probe the benchmark's own harness source explicitly marks 'OPEN CHEMISTRY QUESTION, not scored pass/fail')",
            "dicy_observed_in_committed_and_r_a12_reattack": {"observed_role": "hardener", "observed_reactive_amine_hydrogen_count": 4},
            "dicy_observed_in_my_rerun": {"observed_role": "out_of_domain", "observed_reactive_amine_hydrogen_count": 0},
            "scored_fields_identical": {
                "n_pass": "9/9 in both",
                "n_disagreements": "0 in both",
                "n_scored_probes": "9 in both",
                "verdict": "HYPOTHESIS_CORROBORATED in both",
            },
            "root_cause_analysis": (
                "bridge.cc currently contains is_amidine_or_guanidine_carbon (lines "
                "67-85 of amphora-rdkit-ffi/src/bridge.cc), an exclusion rule explicitly "
                "attributed to role-ranker's own R-N02 C=N fix, which correctly zeroes "
                "DICY's guanidine-adjacent N-H under the rule AS CURRENTLY WRITTEN. My "
                "rerun (0H, out_of_domain) is what that current source produces; hand-"
                "verified by inspection of DICY's SMILES (NC(=N)NC#N): both its NH2 and "
                "bridging NH neighbor the same guanidine carbon, which bears a C=N bond, "
                "so both are excluded under the rule as written. The committed "
                "diagnostic.canonical.json (written 2026-08-02) and R-A12's own "
                "probe_reattack_runA.json (2026-08-03, same day as R-A12) both instead "
                "record hardener/4H -- the pre-fix behavior. The compiled harness "
                "binary's file mtime (2026-08-03T21:40:26Z) postdates the written "
                "diagnostic record, and the linked RDKit .so libraries are unchanged "
                "since 2026-07-18, so the discrepancy is not explained by a library "
                "swap or by any action taken in this fire; the most likely explanation "
                "is that bridge.cc's static archive was linked into this exact binary "
                "at a point that, contrary to file-mtime ordering, did not yet include "
                "the exclusion rule text that is present in the CURRENT bridge.cc, and "
                "the source has since been further edited without the harness being "
                "rebuilt again -- i.e. an infra/build-cache provenance gap on the "
                "OTHER reinstated artifact, not a science error and not decision-"
                "relevant, since the affected probe was never scored."),
            "conclusion": (
                "PARTIAL CAVEAT, NOT A REFUTATION: this is a real reproducibility crack "
                "on the live-runtime-probe artifact's 'byte-exact reproducibility' self-"
                "check claim, but it is fully confined to the single probe the "
                "benchmark's own pre-registered design already excludes from scoring "
                "(DICY's tautomeric/mechanistic ambiguity is explicitly documented in "
                "the harness source as an open question, not a falsifiable claim). "
                "Every scored field (n_pass, n_disagreements, verdict) reproduces "
                "identically. The pre-registered refute criterion for this check "
                "(disagreement in any SCORED field) was not met."),
        },
    },
    "verdict": "CLAIM_SURVIVED",
    "why": (
        "All 5 checks ran. (1) and (2) confirm R-A12's core repair claim -- the "
        "original defect really is wrong-key-not-wrong-science, and the reissue "
        "really is trust-anchored. (3) the reactivity-ratio science reproduces fully "
        "byte-exact with zero caveats. (4) a genuine escalation beyond both R-A12's "
        "and the original benchmark's scope (positive substitution effect, the "
        "chemically plausible regime for the ALIPHATIC hardeners this benchmark "
        "actually tests) found zero reversals across 12 fresh-seeded trials -- this "
        "attack was capable of falsifying (any single reversal would have refuted "
        "H2) and did not. (5) surfaced a real but non-decision-relevant reproducibility "
        "gap on the OTHER reinstated artifact, confined entirely to the one probe the "
        "benchmark itself pre-registered as an unscored open question; every scored "
        "number reproduces identically. None of the pre-registered refute triggers "
        "fired. R-A12's claim withstands this independent verification."
    ),
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (this is an AUDIT_ONLY science-validation replay, "
        "not a Phase-0 evaluation/review signature).",
        "The bridge.cc build/link provenance gap surfaced in check 5: WHY the already-"
        "built role-live-runtime-domain-probe-harness binary's DICY output does not "
        "match its own committed diagnostic or R-A12's own same-day reattack is not "
        "fully root-caused in this fire (candidate cause: a build-cache/relink event "
        "not reflected in file mtimes). Confined to an already-unscored probe; flagged "
        "for module docs/mission.md known-contradictions, not treated as a science "
        "refutation.",
        "Whether reactive_amine_hydrogen_count should be exactly 0 for guanidine N-H "
        "in a quantitative AHEW sense (left open by R-N02 itself, not re-opened here).",
        "Any change to bridge.cc, the KPI receipt, the fixtures, the benchmarks' own "
        "files, or the master manifest (66 receipts/11 modules unchanged; this receipt "
        "reads but does not modify any of them).",
    ],
    "input_artifacts": {
        "r_a12_done_receipt_sha256": r_a12_done_sha,
        "orig_probe_replay_receipt_sha256": orig_probe_sha,
        "orig_reactivity_replay_receipt_sha256": orig_reactivity_sha,
        "reactivity_ratio_script_sha256": reactivity_script_sha,
        "reactivity_canonical_diagnostic_sha256": reactivity_canonical_sha,
        "probe_canonical_diagnostic_sha256": probe_canonical_sha,
        "verify_dsse_script_sha256": verify_dsse_script_sha,
        "escalation_script_sha256": escalation_script_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate_reactivity_rerun": "PASS",
        "two_replay_sha256_gate_escalation": "PASS",
        "escalation_canonical_sha256": escalation_runA_sha,
        "determinism_basis": (
            "reactivity-ratio rerun and escalation: no RNG beyond fixed sha256-derived "
            "seeds, no wall clock; two independent process invocations each produced "
            "byte-identical stdout/output files. live-runtime-probe rerun: no RNG, no "
            "wall clock, but demonstrated NOT stable across sessions -- see results."
        ),
    },
    "rights_check": (
        "No new external data source opened or acquired. All work reads already-in-"
        "tree, already-hash-pinned artifacts and re-executes already-committed or "
        "committed-module-derived scripts; the escalation script imports the "
        "committed run_reactivity_ratio.py's functions after verifying its sha256, "
        "without modifying it."
    ),
    "gates_summary": {
        "two_replay_byte_stable_this_receipt": True,
        "real_production_ffi_used_for_check_5": True,
        "attack_genuinely_capable_of_falsifying": True,
        "escalation_beyond_repair_self_check_performed": True,
        "escalation_beyond_original_benchmark_scope_performed": True,
        "signature_field_is_dsse_envelope_object": True,
        "honest_caveat_reported_not_suppressed": True,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY verify done-receipt under evidence/phase0/repairs/V-A12a/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(WORK / "receipt_body.canonical.json").write_bytes(body1)
(WORK / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-role-ranker.v-a12a-independent-verify-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

DONE.mkdir(parents=True, exist_ok=True)
outpath = DONE / "v-a12a-molecule-role-ranker-independent-verify-receipt.v1.dsse.json"
outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

written = json.loads(outpath.read_text())
sig_env = written["signature"]
payload = base64.standard_b64decode(sig_env["payload"])
sig_bytes = base64.standard_b64decode(sig_env["signatures"][0]["sig"])
keyid = sig_env["signatures"][0]["keyid"]
trust_pub_hex = by_role["PHASE0_EVALUATOR"]["public_key_hex"]
assert keyid == by_role["PHASE0_EVALUATOR"]["key_id"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust_pub_hex)).verify(
    sig_bytes, pae(sig_env["payloadType"], payload))
assert payload == body1

print("WROTE", outpath)
print("verdict", body_obj["verdict"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_byte_identical", body1 == body2)
print("independent_reverify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
