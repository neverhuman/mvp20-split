#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-design-gate
design-gate-oxirane-steric-hostile-null-v1 AUDIT_ONLY falsification receipt.

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
BENCH = ROOT / "amphora-molecule-design-gate/evidence/audit/design-gate-oxirane-steric-hostile-null-v1"
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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

assert diag["n_refutations"] == 2, "expected 2 refutations (tetramethyloxirane + trimethyloxirane)"
refuted_ids = {r["id"] for r in diag["refutations"]}
assert refuted_ids == {"tetramethyloxirane-hostile-null", "trimethyloxirane-gradation-null"}, refuted_ids
assert diag["n_probes"] == 4
assert diag["n_matches_mechanistic_expectation"] == 2

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
    "schema": "amphora.molecule-design-gate.oxirane-steric-hostile-null-receipt.v1",
    "study_id": "design-gate-oxirane-steric-hostile-null-v1",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "REAL_ARITHMETIC",
    "run_type": "adversarial_falsification_attempt_live_production_code",
    "module": "amphora-molecule-design-gate",
    "fire_id": "20260819T010001-1845365-81d2a6944875",
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
                "unauthorized inputs) with a RESIN-SIDE hostile null grounded in a physical "
                "mechanism (steric shielding of a hindered oxirane against nucleophilic "
                "ring-opening by an amine curing agent) not covered by any exclusion clause "
                "in count_oxirane_rings, which is the resin-side twin of the amine-side gap "
                "already found in nitrogen-nucleophilicity-authenticity-v1 (electronic) and "
                "steric-shielded-amine-hostile-null-v1 (steric) but on the OTHER declared "
                "role and never previously attacked."),
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
    "refutation_criterion": ("A commercially available, non-resin, fully- or highly-"
                              "substituted small-molecule epoxide that lacks the glycidyl-"
                              "ether -CH2-O- motif this module's own theory anchor "
                              "(Wicks/Jones/Pappas 2007 Sec.15.2-15.4) requires for "
                              "amine-cure reactivity reaches SCORED status with "
                              "gates.role_appropriate_reactivity == true when declared "
                              "role=resin."),
    "refutation_criterion_occurred": True,
    "mechanism_root_cause": {
        "file": "amphora-rdkit-ffi/src/bridge.cc",
        "function": "count_oxirane_rings",
        "sha256": bridge_cc_sha,
        "finding": ("count_oxirane_rings tests only ring topology: an oxygen of degree 2 and "
                    "formal charge 0, bonded by two single bonds to two carbons that are "
                    "themselves singly bonded. It carries NO exclusion clause of any kind -- "
                    "unlike count_reactive_amine_hydrogens, which after two prior fires "
                    "carries four electronic exclusion clauses (carbonyl/sulfonyl neighbor, "
                    "amidine/guanidine conjugation, formal charge) and still lacks a steric "
                    "one. The oxirane counter has zero exclusions of either kind: it does not "
                    "distinguish a terminal, unhindered glycidyl-ether epoxide carbon (the "
                    "motif every real DGEBA/novolac/PGE coating resin actually presents) from "
                    "a fully quaternary-substituted epoxide carbon with no accessible face for "
                    "backside nucleophilic attack."),
        "not_closed_by_prior_findings": ("nitrogen-nucleophilicity-authenticity-v1 and "
                                          "steric-shielded-amine-hostile-null-v1 both attack "
                                          "count_reactive_amine_hydrogens (the HARDENER-side "
                                          "counter); neither touches count_oxirane_rings (the "
                                          "RESIN-side counter), which was previously verified "
                                          "only for ring-membership/ring-size specificity "
                                          "(rdkit-structural-facts-parity-v1 G3: aziridine/"
                                          "thiirane/cyclopropane/oxetane/THF/ether all "
                                          "correctly excluded) -- never for substitution "
                                          "within a genuine 3-membered O,C,C ring."),
    },
    "probes": diag["results"],
    "refutations": diag["refutations"],
    "results_summary": {
        "n_probes": diag["n_probes"],
        "n_matches_mechanistic_expectation": diag["n_matches_mechanistic_expectation"],
        "n_refutations": diag["n_refutations"],
        "backend_status": diag["backend_status"],
    },
    "headline_result": ("CLAIM_REFUTED: 2/4 live-RDKit-FFI probes diverge. "
                        "2,2,3,3-tetramethyloxirane (tetramethylethylene oxide, CAS "
                        "5076-20-0, both epoxide carbons quaternary, zero ring C-H) and "
                        "2,2,3-trimethyloxirane (2,3-epoxy-2-methylbutane, CAS 5076-19-7, one "
                        "epoxide carbon quaternary) both reach SCORED with "
                        "role_appropriate_reactivity=true when declared role=resin, despite "
                        "neither being sold, classified, or usable as a two-part epoxy-amine "
                        "coating resin by any supplier -- both are small-molecule synthesis "
                        "reagents whose fully-substituted epoxide carbons sterically block "
                        "the nucleophilic ring-opening amine cure depends on. Internal "
                        "controls confirm specificity: phenyl glycidyl ether (a real, "
                        "commercially marketed epoxy reactive diluent with an unhindered "
                        "terminal glycidyl carbon) correctly reached SCORED, and oxetane (a "
                        "four-membered, non-oxirane cyclic ether) correctly FAILED_GATES via "
                        "the pre-existing ring-size clause -- isolating the defect to "
                        "substitution-blindness strictly within valid 3-membered rings."),
    "provenance": {
        "harness_main_rs_sha256": main_rs_sha,
        "harness_main_rs_path": ("amphora-molecule-design-gate/evidence/audit/"
                                  "design-gate-oxirane-steric-hostile-null-v1/work/harness/"
                                  "src/main.rs"),
        "production_entry_points": [
            "amphora_rdkit_ffi::molecule_facts (real pinned RDKit C++ 2026.03.2 FFI)",
            "amphora_molecule_capabilities::capability(DESIGN_GATE_ID).evaluate_authorized",
        ],
        "prior_receipts": [
            "amphora-molecule-design-gate/evidence/audit/nitrogen-nucleophilicity-authenticity-v1",
            "amphora-molecule-design-gate/evidence/audit/steric-shielded-amine-hostile-null-v1/steric-shielded-amine-hostile-null-receipt.v1.dsse.json",
            "amphora-molecule-design-gate/evidence/audit/rdkit-structural-facts-parity-v1",
        ],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "per_probe_two_replay_all_true": all(
            r["per_call_two_replay_byte_stable"] for r in diag["results"]),
        "rdkit_backend_status": diag["backend_status"],
    },
    "proposed_followups": [
        {
            "id": "R-DESIGNGATE-OXIRANE-STERIC",
            "gap": ("count_oxirane_rings has no substitution/steric exclusion clause of any "
                    "kind; fully- or highly-substituted small-molecule epoxides lacking the "
                    "glycidyl-ether motif are mis-admitted as coating resins."),
            "proposed_repair_criterion": ("Add a substitution-pattern clause to bridge.cc "
                                           "(e.g. require at least one epoxide ring carbon to "
                                           "carry a hydrogen -- the standard structural proxy "
                                           "distinguishing a glycidyl-type terminal/internal "
                                           "epoxide from a fully-substituted one) or an "
                                           "explicit glycidyl-ether substructure match, add "
                                           "hindered-epoxide fixture records (tetramethyl- and "
                                           "trimethyloxirane as negative exemplars, PGE/DGEBA "
                                           "as positive exemplars), and re-run this exact "
                                           "harness (same 4 probes, same SMILES) as the "
                                           "acceptance check; must not flip any of the 42 "
                                           "existing fixture labels or the T-08 held-out "
                                           "probes (non-regression)."),
        },
    ],
    "closes": [],
    "does_not_close": [
        "Wiring the steric clause into the live Rust/C++ runtime (src mutation requires a "
        "dedicated repair item with its own re-attack per repair-mode protocol)",
        "Whether other steric or electronic motifs beyond the two probed substitution grades "
        "(e.g. neopentyl-type beta-branching adjacent to, but not on, the epoxide ring) are "
        "also mis-admitted",
        "The unrelated, already-recorded implementation-source-hash-binding-integrity defect "
        "in mission.md/capability-profile.json (REFUTED 2026-08-17, still unrepaired as of "
        "this fire) -- out of scope for this attack, not reopened here.",
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
ptype = "application/vnd.amphora.molecule-design-gate-oxirane-steric-hostile-null+json"
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
out = BENCH / "design-gate-oxirane-steric-hostile-null-receipt.v1.dsse.json"
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
