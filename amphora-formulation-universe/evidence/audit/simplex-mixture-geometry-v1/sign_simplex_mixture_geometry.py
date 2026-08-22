#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-formulation-universe simplex-mixture-geometry
AUDIT_ONLY receipt. Signs an audit receipt under evidence/audit/; does NOT sign
a phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the portfolio manifest (66 receipts / 11
modules), any locked dataset, the signed Phase-0 formulation-universe KPI, or
the live Rust engine. Derived evaluator key_id cross-checked against the pinned
trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-formulation-universe/evidence/audit/simplex-mixture-geometry-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
KPI = ROOT / "amphora-formulation-universe/evidence/phase0/kpis/formulation-universe-cartesian-accounting-kpi.v1.json"
FIXTURE = ROOT / "amphora-formulation-universe/reference/phase0-formulation-universe-known-answer.v1.json"
ANCHORS = ROOT / "amphora-formulation-universe/reference/mvp20/data/formulation_mixture_region_anchors.v1.json"
PRIOR = ROOT / ("amphora-formulation-universe/evidence/audit/mixed-radix-bijection-v1/"
                "mixed-radix-bijection-receipt.v1.dsse.json")


def sha(b): return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try: return bytes.fromhex(raw.decode())
        except Exception: pass
    return raw[:32]


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["acceptance_all_perfect"], "acceptance not all perfect"
assert diag["gates_pass"] == diag["gates_total"], "a gate regressed"
assert diag["failclosed_probe_pass"] == diag["failclosed_probe_total"], \
    "fail-closed probe leaked"
harness_sha = sha((BENCH / "run_simplex_mixture_geometry.py").read_bytes())
anchors_sha = sha(ANCHORS.read_bytes())
assert diag["anchor_dataset"]["sha256"] == anchors_sha, "anchor dataset drifted"
kpi_sha = sha(KPI.read_bytes()) if KPI.exists() else None
fixture_sha = sha(FIXTURE.read_bytes())
prior_sha = sha(PRIOR.read_bytes()) if PRIOR.exists() else None

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw(); eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.formulation-universe.simplex-mixture-geometry-receipt.v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-formulation-universe",
    "axis": "THEORY",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_live_rust_engine": False,
    "baselines": [
        {"source": "Scheffe, H. (1958) Experiments with Mixtures, JRSS-B 20(2):344-360",
         "doi": "10.1111/j.2517-6161.1958.tb00299.x",
         "used_for": "simplex-lattice {q,m}; |{q,m}| = C(q+m-1,m); canonical polynomial saturation"},
        {"source": "Scheffe, H. (1963) The Simplex-Centroid Design, JRSS-B 25(2):235-263",
         "doi": "10.1111/j.2517-6161.1963.tb00506.x",
         "used_for": "simplex-centroid design; 2^q - 1 points"},
        {"source": "McLean, R.A. & Anderson, V.L. (1966) Extreme Vertices Design of Mixture Experiments, Technometrics 8(3):447-454",
         "doi": "10.1080/00401706.1966.10490377",
         "used_for": "extreme-vertices generator for bound-constrained mixture regions"},
        {"source": "Snee, R.D. & Marquardt, D.W. (1974) Extreme Vertices Designs for Linear Mixture Models, Technometrics 16(3):399-408",
         "doi": "10.1080/00401706.1974.10489209",
         "used_for": "over-generation caveat on the McLean-Anderson generator"},
        {"source": "Piepel, G.F. (1983) Defining Consistent Constraint Regions in Mixture Experiments, Technometrics 25(1):97-101",
         "doi": "10.1080/00401706.1983.10487825",
         "used_for": "consistency predicate and implied-bound range identity"},
        {"source": "Motzkin, Raiffa, Thompson & Thrall (1953) The Double Description Method, Annals of Math. Studies 28",
         "isbn": "978-0-691-07935-6",
         "used_for": "independent vertex-enumeration parity oracle"},
        {"source": "Cornell, J.A. (2002) Experiments with Mixtures, 3rd ed., Wiley",
         "isbn": "0-471-07916-2",
         "used_for": "consolidated closed forms incl. special-cubic term count"},
    ],
    "diagnostic": diag,
    "provenance": {
        "signed_phase0_kpi_sha256": kpi_sha,
        "known_answer_fixture_sha256": fixture_sha,
        "anchor_dataset_sha256": anchors_sha,
        "anchor_dataset_path": "amphora-formulation-universe/reference/mvp20/data/formulation_mixture_region_anchors.v1.json",
        "anchor_dataset_license": "CC0-1.0",
        "prior_audit_receipt_sha256": prior_sha,
        "prior_audit_receipt_path": "amphora-formulation-universe/evidence/audit/mixed-radix-bijection-v1/mixed-radix-bijection-receipt.v1.dsse.json",
        "harness_sha256": harness_sha,
        "adds": ("The Phase-0 benchmark and the prior mixed-radix bijection oracle "
                 "both certify CARTESIAN accounting over categorical axes. This "
                 "receipt adds the mixture geometry that Cartesian accounting "
                 "cannot express: the closure constraint sum(x)=1. It (i) "
                 "re-derives the Scheffe 1958/1963 simplex-lattice and "
                 "simplex-centroid point counts and canonical term counts by "
                 "brute-force exact enumeration, (ii) proves {q,m} saturation by "
                 "an exact rational determinant of the canonical model matrix, "
                 "(iii) shows that filtering the mixed-radix Cartesian grid by "
                 "closure yields exactly the Scheffe lattice and quantifies how "
                 "much of the module's cardinality ceiling closure-infeasible "
                 "points consume, and (iv) certifies the extreme-vertex set of "
                 "six coating constrained-mixture regions by two independent "
                 "published algorithms plus the Piepel 1983 implied-bound range "
                 "identity."),
    },
    "phase1_implication": (
        "For closed composition axes the Cartesian generator is loss-free but "
        "wasteful: at q=6, m=6 only 0.392694% of the 117649 enumerated grid "
        "points satisfy closure, and 3 of 8 audited cases breach "
        "MAX_FORMULATION_UNIVERSE_CARDINALITY=10000 in Cartesian form while the "
        "equivalent Scheffe lattice fits comfortably. A Phase-1 "
        "simplex-lattice / extreme-vertices generator would deliver identical "
        "design coverage inside the existing ceiling. This receipt does not "
        "authorise that change; it is AUDIT_ONLY evidence for it."),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "determinism_basis": ("exact rational arithmetic (fractions.Fraction), "
                              "no floating-point decisions, no randomness, no "
                              "network, sorted canonical JSON"),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.formulation-universe-simplex-mixture-geometry+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "simplex-mixture-geometry-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("anchor_dataset_sha256", anchors_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
