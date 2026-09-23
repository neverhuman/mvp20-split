#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-design-gate
steric-shielded-amine-hostile-null-v1 AUDIT_ONLY falsification receipt.

AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest, module-manifest.json,
any locked dataset, the design-gate fixture, or a signed Phase-0 KPI, and does
NOT modify the live Rust runtime. Derived key_id cross-checked vs pinned trust
store."""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-design-gate/evidence/audit/steric-shielded-amine-hostile-null-v1"
HARNESS = BENCH / "work/harness"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
MAIN_RS = HARNESS / "src/main.rs"
BRIDGE_CC = ROOT / "amphora-rdkit-ffi/src/bridge.cc"
KPI_FILE = ROOT / "amphora-molecule-design-gate/evidence/phase0/kpis/design-gate-structural-applicability-kpi.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (HARNESS / "diagnostic.canonical.json").read_bytes()
runB = (HARNESS / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

assert diag["n_refutations"] == 2, "expected 2 refutations (TEMP + Tinuvin 770)"
refuted_ids = {r["id"] for r in diag["refutations"]}
assert refuted_ids == {"temp-2266-tetramethylpiperidine", "tinuvin770-hals-diester"}, refuted_ids

main_rs_sha = sha(MAIN_RS.read_bytes())
bridge_cc_sha = sha(BRIDGE_CC.read_bytes())
kpi_sha = sha(KPI_FILE.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw()
rev_pub_hex = rev_pub.hex()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.molecule-design-gate.steric-shielded-amine-hostile-null-receipt.v1",
    "study_id": "steric-shielded-amine-hostile-null-v1",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "REAL_ARITHMETIC",
    "run_type": "adversarial_falsification_attempt_live_production_code",
    "module": "amphora-molecule-design-gate",
    "fire_id": "20260815T130001-2643701-d144018cf282",
    "campaign_item_id": "",
    "mode": "ROTATION",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_design_gate_fixture": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_live_rust_runtime": False,
    "purpose": ("Falsify the design gate's structural-applicability KPI and mission.md "
                "primary KPI (negative-control rejection / zero silent acceptance of "
                "unauthorized inputs) with a hostile null grounded in a physical mechanism "
                "(steric shielding of a hindered secondary amine) not covered by any "
                "existing exclusion clause in the shipped rule or the prior "
                "nitrogen-nucleophilicity-authenticity-v1 refined predicate."),
    "claim_under_attack": {
        "kpi_path": "evidence/phase0/kpis/design-gate-structural-applicability-kpi.v1.json",
        "kpi_sha256": kpi_sha,
        "kpi_theory_quote": ("Structural applicability for role X iff the molecule carries "
                              "reactive group Y ... Every supplier TDS embeds the same "
                              "accept/reject filter before quoting mix ratios."),
        "mission_md_primary_kpi_quote": ("negative-control rejection at gates.pass_all_hard "
                                          "... Locked target: Zero silent acceptance of "
                                          "malformed, unsupported, or unauthorized inputs "
                                          "before Phase 0."),
    },
    "refutation_criterion": ("A real, named, currently-marketed coating additive that no "
                              "supplier TDS sells or classifies as an epoxy-amine hardener "
                              "reaches SCORED status with gates.role_appropriate_reactivity "
                              "== true when declared role=hardener."),
    "refutation_criterion_occurred": True,
    "mechanism_root_cause": {
        "file": "amphora-rdkit-ffi/src/bridge.cc",
        "function": "count_reactive_amine_hydrogens",
        "sha256": bridge_cc_sha,
        "finding": ("Exclusion clauses cover only electronic effects (carbonyl/sulfonyl "
                    "neighbor, amidine/guanidine conjugation, formal charge). No steric "
                    "clause exists. A neutral, non-aromatic, non-conjugated secondary-amine "
                    "N-H with no disqualifying neighbor atom is counted as reactive "
                    "regardless of steric accessibility."),
        "not_closed_by_prior_finding": ("evidence/audit/nitrogen-nucleophilicity-"
                                         "authenticity-v1's 6-clause refined predicate is "
                                         "purely electronic and does not address sterics; "
                                         "its README explicitly scopes out only "
                                         "alpha-heteroatom amines and delocalized "
                                         "amidine/guanidine N-H."),
    },
    "probes": diag["results"],
    "refutations": diag["refutations"],
    "results_summary": {
        "n_probes": diag["n_probes"],
        "n_matches_mechanistic_expectation": diag["n_matches_mechanistic_expectation"],
        "n_refutations": diag["n_refutations"],
        "backend_status": diag["backend_status"],
    },
    "headline_result": ("CLAIM_REFUTED: 2/4 live-RDKit-FFI probes diverge. TEMP "
                        "(2,2,6,6-tetramethylpiperidine, CAS 768-66-1, N-H count 1) and "
                        "Tinuvin 770 (bis(2,2,6,6-tetramethyl-4-piperidyl) sebacate, BASF, "
                        "CAS 52829-07-9, a real marine-topcoat UV light stabilizer, N-H "
                        "count 2) both reach SCORED with role_appropriate_reactivity=true "
                        "when declared role=hardener, despite neither being nucleophilic "
                        "nor sold/classified as a hardener by any supplier. Internal "
                        "controls confirm specificity: the N-methylated tertiary analog "
                        "(Tinuvin 292, N-H count 0) correctly FAILED_GATES via the "
                        "pre-existing tertiary-amine exclusion, and the unhindered "
                        "secondary amine control (piperidine) correctly SCOREd."),
    "provenance": {
        "harness_main_rs_sha256": main_rs_sha,
        "harness_main_rs_path": ("amphora-molecule-design-gate/evidence/audit/"
                                  "steric-shielded-amine-hostile-null-v1/work/harness/src/main.rs"),
        "production_entry_points": [
            "amphora_rdkit_ffi::molecule_facts (real pinned RDKit C++ 2026.03.2 FFI)",
            "amphora_molecule_capabilities::capability(DESIGN_GATE_ID).evaluate_authorized",
        ],
        "prior_receipts": [
            "amphora-molecule-design-gate/evidence/audit/nitrogen-nucleophilicity-authenticity-v1",
            "amphora-molecule-design-gate/evidence/phase0/repairs/T-08/done/t08-design-gate-live-runtime-adversarial-receipt.v1.dsse.json",
        ],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "per_probe_two_replay_all_true": all(
            r["per_call_two_replay_byte_stable"] for r in diag["results"]),
    },
    "proposed_followups": [
        {
            "id": "R-DESIGNGATE-STERIC",
            "gap": ("count_reactive_amine_hydrogens has no steric-shielding exclusion "
                    "clause; sterically hindered 2,2,6,6-tetramethylpiperidine-class "
                    "secondary amines (HALS) are mis-admitted as hardeners."),
            "proposed_repair_criterion": ("Add a neighbor-substitution-count clause (e.g. "
                                           "both alpha-carbons of the amine nitrogen fully "
                                           "substituted / quaternary, a standard steric proxy "
                                           "used for HALS/2,2,6,6-tetramethylpiperidine "
                                           "classification) to bridge.cc, add HALS fixture "
                                           "records, and re-run this exact harness (same "
                                           "probes, same SMILES) as the acceptance check; "
                                           "must not flip any of the 42 existing fixture "
                                           "labels or the T-08 held-out probes (non-regression)."),
        },
    ],
    "closes": [],
    "does_not_close": [
        "Wiring the steric clause into the live Rust/C++ runtime (src mutation requires a "
        "dedicated repair item with its own re-attack per repair-mode protocol)",
        "Whether other steric motifs beyond 2,2,6,6-tetramethylpiperidine (e.g. other "
        "ortho,ortho'-disubstituted anilines) are also mis-admitted",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY falsification receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": ("Reviewer key referenced for provenance only; no independent human review "
                 "performed."),
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-design-gate-steric-shielded-amine-hostile-null+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id,
                    "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}
out = BENCH / "steric-shielded-amine-hostile-null-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("bridge_cc_sha256", bridge_cc_sha)
print("kpi_sha256", kpi_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
