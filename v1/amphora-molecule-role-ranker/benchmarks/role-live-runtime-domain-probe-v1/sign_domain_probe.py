"""DSSE-Ed25519-sign the role-live-runtime-domain-probe-v1 replay receipt.

Falsification attack: invokes the REAL production RDKit C++ FFI
(amphora-rdkit-ffi::molecule_facts, pinned RDKit 2026.03.2, the exact
bridge.cc count_oxirane_rings / count_reactive_amine_hydrogens logic the
live checked amphora-molecule-role-ranker runtime consumes) on 10 real,
named, cited, coating-relevant molecules held out of the module's
self-authored 39-record known-answer fixture. Signs the byte-identical
two-replay canonical diagnostic with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY
Ed25519 key (local-9028773f..., NOT the trust-anchored phase0-evaluator
key). AUDIT_ONLY: does NOT promote the module, does NOT edit the master
manifest, does NOT close EVALUATION_SIGNATURE_ABSENT.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-molecule-role-ranker/benchmarks/role-live-runtime-domain-probe-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANON_SHA = "9b03c2da5777e9578e8dadb1c32f4ab89e99af40546ba48d777d91f9bd6b7360"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


cb = (BENCH / "diagnostic.canonical.json").read_bytes()
rb = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(cb) == CANON_SHA, f"{sha(cb)} != {CANON_SHA}"
assert sha(rb) == CANON_SHA, f"runB {sha(rb)} != {CANON_SHA} (two-replay gate)"
diag = json.loads(cb)
harness_main_sha = sha((BENCH / "harness/src/main.rs").read_bytes())
harness_cargo_sha = sha((BENCH / "harness/Cargo.toml").read_bytes())

scored = [r for r in diag["results"] if r["scored"]]
open_q = [r for r in diag["results"] if not r["scored"]]

receipt = {
    "schema": "amphora.molecule-role-ranker.role-live-runtime-domain-probe-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-molecule-role-ranker",
    "benchmark": "amphora-molecule-role-ranker/role-live-runtime-domain-probe-v1",
    "axis": "LIVE_RUNTIME_GENERALIZATION",
    "purpose": diag["purpose"],
    "attack_design": (
        "Falsification target: the flagship Phase-0 KPI "
        "(evidence/phase0/kpis/role-classification-kpi.v1.json) asserts "
        "structural_inference_agreement_rate=1.0 (24/24), scored entirely on the "
        "module's own self-authored CC0 39-record fixture. That fixture was "
        "authored by the same lineage that wrote the classification rule, so "
        "in-sample agreement does not bound out-of-sample error on real named "
        "commercial/literature epoxy-amine coating chemistry. This benchmark "
        "invokes the REAL compiled production chemistry backend directly -- "
        "not a from-scratch Python SMARTS re-derivation as in the module's "
        "prior role-fact-provenance-invariance-v1 receipt -- on 10 held-out, "
        "cited, real molecules chosen to stress every branch of "
        "bridge.cc::count_reactive_amine_hydrogens / count_oxirane_rings: "
        "an ester-adjacent cycloaliphatic diepoxide resin, an ether-backbone "
        "diamine, a mixed primary/secondary/tertiary-nitrogen piperazine, a "
        "secondary amine whose alpha-carbon (not the amine nitrogen) bears a "
        "direct ester substituent (aspartic-ester hardener class), a real "
        "tertiary-amine cure accelerator and a real aromatic-heterocycle "
        "latent hardener (both must fail closed as out_of_domain, not be "
        "silently promoted to hardener stoichiometry), a diamine with an "
        "unrelated distant sulfone group, and two aromatic diamines "
        "(unhindered and sterically hindered). A single disagreement on any "
        "scored probe falsifies the generalization implicit in the flagship "
        "KPI's 1.0 agreement-rate framing."
    ),
    "toolkit_provenance": diag["toolkit_provenance"],
    "probes": [
        {
            "id": r["id"],
            "smiles": r["smiles"],
            "canonical_isomeric_smiles": r["canonical_isomeric_smiles"],
            "citation": r["citation"],
            "note": r["note"],
            "formula": r["formula"],
            "average_molecular_weight_g_mol": r["average_molecular_weight_g_mol"],
            "scored": r["scored"],
            "expected": {
                "oxirane_ring_count": r["expected_oxirane_ring_count"],
                "reactive_amine_hydrogen_count": r["expected_reactive_amine_hydrogen_count"],
                "role": r["expected_role"],
            },
            "observed": {
                "oxirane_ring_count": r["observed_oxirane_ring_count"],
                "reactive_amine_hydrogen_count": r["observed_reactive_amine_hydrogen_count"],
                "role": r["observed_role"],
            },
            "pass": r["pass"],
        }
        for r in diag["results"]
    ],
    "headline_result": {
        "n_scored_probes": diag["summary"]["n_scored_probes"],
        "n_pass": diag["summary"]["n_pass"],
        "n_disagreements": diag["summary"]["n_disagreements"],
        "n_open_question_probes_not_scored": diag["summary"]["n_open_question_probes_not_scored"],
        "open_question_probe_ids": [r["id"] for r in open_q],
        "verdict": diag["verdict"],
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2,
        "independent_runs": True,
        "canonical_diagnostic_sha256": CANON_SHA,
        "runB_diagnostic_sha256": sha(rb),
        "harness_main_rs_sha256": harness_main_sha,
        "harness_cargo_toml_sha256": harness_cargo_sha,
        "harness_binary_provenance": (
            "cargo build --release against amphora-rdkit-ffi (path dependency, "
            "feature=rdkit) compiled with cxx against the pinned RDKit 2026.03.2 "
            "prefix at /home/ubuntu/.local/share/amphora/rdkit-2026.03.2 "
            "(RDKIT_INCLUDE_DIR/RDKIT_LIB_DIR/BOOST_INCLUDE_DIR); backend_status()."
            "exact_version_match=true recorded in toolkit_provenance."
        ),
        "determinism_basis": (
            "no RNG, no wall-clock, fixed hardcoded probe list, serde_json BTreeMap "
            "key ordering (preserve_order feature not enabled) => canonical byte "
            "order every run; two independent process invocations produced "
            "byte-identical stdout (sha256 equal)."
        ),
        "fixture_disjointness": (
            "none of the 10 probe SMILES canonicalize to any of the 39 fixture "
            "records' canonical SMILES (phase0-role-known-answer.v1.json, sha "
            "8ce4d54192a20e8de1bb89f6181b11630fc184b4dda2918ce934610630855c8f); "
            "verified by inspection against the fixture's record list."
        ),
    },
    "closes": [
        "Whether the live production RDKit C++ FFI backend (not a Python "
        "re-derivation) agrees with structurally hand-derived, literature-cited "
        "ground truth on real coating-relevant molecules outside the "
        "self-authored fixture, across carbonyl-exclusion, sulfonyl-exclusion, "
        "aromatic-exclusion, and multi-nitrogen-class edge cases.",
    ],
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0-evaluator key absent "
        "on this host by governance; local audit key only).",
        "Phase-1 needs an independent double-labelled expert reference set; this "
        "receipt's ground truth is hand-derived by the attacking agent from "
        "cited public compound identities (CAS/PubChem), not a second labeller.",
        "DICY (dicyandiamide) probe is recorded as an open chemistry question, "
        "not scored: its real cure mechanism (catalysed nitrile addition/"
        "cyclisation) does not reduce to simple N-H:epoxide stoichiometry, so "
        "there is no uncontested ground truth for reactive_amine_hydrogen_count "
        "in the AHEW sense. Flagged for docs/mission.md known-contradictions, "
        "not treated as a refutation.",
        "Only 10 probes; does not exhaustively cover the reactive-function "
        "ontology (e.g. no phosphoramide, no charged/zwitterionic species, no "
        "isotope-labelled input).",
    ],
    "phase0_gap_ledger": {
        "EVALUATION_SIGNATURE_ABSENT": "trust-anchored phase0-evaluator private key absent on host (governance, not a build step)",
        "MANIFEST_UNCHANGED": "master receipts manifest (66 receipts / 11 modules) NOT edited; requires human dual-identity Phase-0 ceremony keys",
        "SCOPE": "generalization probe of the live production chemistry backend beyond the self-authored fixture; ground truth is agent-derived from cited public compound identity, not independently expert-labelled",
    },
    "claim_locks": [
        "role_classification_kpi_flagship_generalizes_beyond_self_authored_fixture",
    ],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-role-ranker-role-live-runtime-domain-probe+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signature": sig_b64,
    "signatures": [{"keyid": PUB["key_id"], "sig": sig_b64}],
}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("verdict", receipt["headline_result"]["verdict"])
print("n_pass/n_scored", receipt["headline_result"]["n_pass"], "/", receipt["headline_result"]["n_scored_probes"])
