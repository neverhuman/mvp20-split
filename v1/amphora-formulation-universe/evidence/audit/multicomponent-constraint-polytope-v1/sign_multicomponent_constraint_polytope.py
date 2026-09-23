#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-formulation-universe
multicomponent-constraint-polytope AUDIT_ONLY receipt. Signs an audit receipt
under evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT
promote authority, does NOT flip scientific_readiness, does NOT modify the
portfolio manifest (66 receipts / 11 modules), any locked dataset, the signed
Phase-0 formulation-universe KPI, or the live Rust engine. Derived evaluator
key_id cross-checked against the pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / ("amphora-formulation-universe/evidence/audit/"
                "multicomponent-constraint-polytope-v1")
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
KPI = ROOT / ("amphora-formulation-universe/evidence/phase0/kpis/"
              "formulation-universe-cartesian-accounting-kpi.v1.json")
FIXTURE = ROOT / ("amphora-formulation-universe/reference/"
                  "phase0-formulation-universe-known-answer.v1.json")
ANCHORS = ROOT / ("amphora-formulation-universe/reference/mvp20/data/"
                  "formulation_multicomponent_constraint_anchors.v1.json")
PRIOR = ROOT / ("amphora-formulation-universe/evidence/audit/"
                "simplex-mixture-geometry-v1/"
                "simplex-mixture-geometry-receipt.v1.dsse.json")


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
assert diag["headline"]["snee_marquardt_h0_vertex_completeness_refuted"], \
    "H0 refutation claim not supported by diagnostic"
harness_sha = sha((BENCH / "run_multicomponent_constraint_polytope.py").read_bytes())
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
    "schema": ("amphora.formulation-universe."
               "multicomponent-constraint-polytope-receipt.v1"),
    "authority": "AUDIT_ONLY",
    "module": "amphora-formulation-universe",
    "axis": "THEORY",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "human_review_performed": False, "organizational_independence_asserted": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False, "modifies_live_rust_engine": False,
    "baselines": [
        {"source": ("Snee, R.D. (1979) Experimental designs for mixture systems "
                    "with multicomponent constraints, Commun. Stat. Theory "
                    "Methods A8(4):303-326"),
         "doi": "10.1080/03610927908827762",
         "used_for": ("extreme-vertex geometry of linearly constrained mixture "
                      "regions; basic-feasible-solution enumeration path")},
        {"source": ("Piepel, G.F. (1988) Programs for generating extreme "
                    "vertices and centroids of linearly constrained "
                    "experimental regions, J. Qual. Technol. 20(2):125-136"),
         "doi": "10.1080/00224065.1988.11979094",
         "used_for": ("CONVRT/CONAEV conformance: face centroid = average of "
                      "vertices on the face; overall centroid feasibility")},
        {"source": ("Snee, R.D. & Marquardt, D.W. (1974) Extreme vertices "
                    "designs for linear mixture models, Technometrics "
                    "16(3):399-408"),
         "doi": "10.1080/00401706.1974.10489209",
         "used_for": ("H0 under test: inadequacy of bound-only candidate "
                      "generation once linear mixture constraints bind")},
        {"source": ("McLean, R.A. & Anderson, V.L. (1966) Extreme Vertices "
                    "Design of Mixture Experiments, Technometrics 8(3):447-454"),
         "doi": "10.1080/00401706.1966.10490377",
         "used_for": "bound-only candidate generator under test"},
        {"source": ("Motzkin, Raiffa, Thompson & Thrall (1953) The Double "
                    "Description Method, Annals of Math. Studies 28"),
         "isbn": "978-0-691-07935-6",
         "used_for": "independent vertex-enumeration parity oracle"},
        {"source": ("Asbeck, W.K. & Van Loo, M. (1949) Critical pigment volume "
                    "relationships, Ind. Eng. Chem. 41(7):1470-1475"),
         "doi": "10.1021/ie50475a042",
         "used_for": ("pigment volume concentration ratio constraint "
                      "linearized to a multicomponent half-space pair")},
        {"source": ("Lee, H. & Neville, K. (1967) Handbook of Epoxy Resins, "
                    "McGraw-Hill"),
         "isbn": "978-0-07-036997-9",
         "used_for": ("amine-H:epoxide stoichiometric index r = "
                      "(x_am/AHEW)/(x_ep/EEW) band constraint")},
        {"source": "Cornell, J.A. (2002) Experiments with Mixtures, 3rd ed., Wiley",
         "isbn": "0-471-07916-2",
         "used_for": "ratio constraints on mixture components"},
    ],
    "diagnostic": diag,
    "provenance": {
        "signed_phase0_kpi_sha256": kpi_sha,
        "known_answer_fixture_sha256": fixture_sha,
        "anchor_dataset_sha256": anchors_sha,
        "anchor_dataset_path": ("amphora-formulation-universe/reference/mvp20/"
                                "data/formulation_multicomponent_constraint_"
                                "anchors.v1.json"),
        "anchor_dataset_license": "CC0-1.0",
        "prior_audit_receipt_sha256": prior_sha,
        "prior_audit_receipt_path": ("amphora-formulation-universe/evidence/"
                                     "audit/simplex-mixture-geometry-v1/"
                                     "simplex-mixture-geometry-receipt.v1."
                                     "dsse.json"),
        "harness_sha256": harness_sha,
        "adds": ("The prior simplex-mixture-geometry receipt certified "
                 "box-bounded mixture regions and honestly recorded that the "
                 "Snee-Marquardt 1974 caveat could not fire with box-only "
                 "bounds. This receipt adds the multicomponent linear "
                 "constraints real coating windows impose: (i) it proves the "
                 "Asbeck-Van Loo PVC band and the Lee-Neville amine-H:epoxide "
                 "stoichiometric band linearize EXACTLY to half-space pairs "
                 "on weight fractions (exact-rational equivalence at every "
                 "test point including band-boundary points); (ii) it "
                 "certifies the extreme-vertex sets of six marine epoxy-amine "
                 "constrained regions by two independent published paths "
                 "(Snee 1979 basic-feasible-solution enumeration vs Motzkin "
                 "1953 sequential double description), 76 vertices, set-equal "
                 "6/6, every vertex rank-certified extreme; (iii) it REFUTES "
                 "H0 (McLean-Anderson bound-only candidate generation stays "
                 "vertex-complete): 6/6 regions refute, 70 of 76 true "
                 "vertices are missing from the MA candidate set and every "
                 "missing vertex lies on a band facet; (iv) Piepel 1988 "
                 "CONAEV centroid identities hold exactly; (v) the degenerate "
                 "1:1 stoichiometry region collapses to affine dimension 1 as "
                 "declared, and box-only vs constrained vertex counts are "
                 "quantified per region."),
    },
    "phase1_implication": (
        "A Phase-1 formulation-universe generator that enumerates candidate "
        "coating windows must use a multicomponent-constraint vertex "
        "algorithm (Snee 1979 / Piepel 1988 CONVRT class, or double "
        "description); bound-only McLean-Anderson generation silently drops "
        "92.1% (70/76) of the audited regions' true extreme formulations the "
        "moment a PVC or stoichiometric band binds. This receipt does not "
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
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": ("Reviewer key referenced for provenance only; no independent "
                 "human review performed.")},
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = ("application/vnd.amphora."
         "formulation-universe-multicomponent-constraint-polytope+json")
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(),
            "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id,
                            "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id,
           "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex,
           "signature": envelope}
out = BENCH / "multicomponent-constraint-polytope-receipt.v1.dsse.json"
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
