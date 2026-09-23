#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-T-DESIGNGATE applicability-domain comparator
receipt for amphora-molecule-design-gate.

REPAIR-MODE output contract for campaign item W-T-DESIGNGATE: this receipt
goes to evidence/phase0/repairs/W-T-DESIGNGATE/done/ because every element of
the done_criterion is satisfied in this single fire: >=5 OECD normative
requirements enumerated (5), one named published AD method implemented
(hat-matrix leverage / Williams plot, Gramatica 2007), every gate-vs-method
disagreement (21 of 55 comparison rows) characterised with a verdict of
conformant/divergent/not_applicable and observed evidence, the baseline cited
with its DOI, and every divergence filed into proposed_followups[] with a
proposed repair criterion. Verdict is CLAIM_REFUTED (not SURVIVED), so the
positive_control block is not required by the campaign item's own rule.

AUDIT_ONLY: does not promote the module, does not flip scientific_readiness
or mission.md front matter, does not modify the master manifest,
module-manifest.json, any locked dataset, the design-gate fixture, or the
live Rust runtime. It DOES append one bullet to mission.md's "Known
contradictions" prose (permitted; logged not fatal per the founder's module
mission.md convention) recording this finding.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-molecule-design-gate/evidence/phase0/repairs/W-T-DESIGNGATE"
WORK = ITEM / "work"
ANALYSIS_SCRIPT = WORK / "wtdg_analysis.py"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
MISSION = ROOT / "amphora-molecule-design-gate/docs/mission.md"
KPI_PATH = ROOT / "amphora-molecule-design-gate/evidence/phase0/kpis/design-gate-structural-applicability-kpi.v1.json"


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


canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay diagnostic bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)

req = diag["oecd_principles_2004_2007"]["requirements"]
assert len(req) >= 5, "done_criterion requires >=5 OECD normative requirements"
summary = diag["summary"]
assert summary["n_total"] == 55
divergent_rows = [c for c in diag["comparator_results"] if c["verdict"] == "divergent"]
assert len(divergent_rows) == summary["n_divergent"] > 0
followups = diag["proposed_followups"]
assert len(followups) == summary["n_divergent"], "every divergence must have a filed followup"
for f in followups:
    assert f["proposed_repair_criterion"], "followup missing a proposed repair criterion"

mission_sha_before = sha(MISSION.read_bytes())

# Append one bullet to the "Known contradictions" prose recording this finding.
mission_text = MISSION.read_text()
anchor = (
    "- The PHASE-0 BINDING GAP named by the founder directive (front-matter "
    '`"phase":"PHASE_0"` vs. this document\'s own prose stating the current phase is '
    "Pre-Phase 0, immediately below) is recorded, not repaired, by T-08; repair needs the "
    "human dual-identity Phase-0 promotion ceremony."
)
assert anchor in mission_text, "anchor bullet not found; refusing to blind-append"
new_bullet = (
    "\n- Campaign item W-T-DESIGNGATE "
    "(`evidence/phase0/repairs/W-T-DESIGNGATE/done/w-t-designgate-ad-comparator-receipt.v1.dsse.json`, "
    "DSSE-signed by `PHASE0_EVALUATOR`) closes the standing theory gap that the module's sole "
    "Phase-0 KPI (`design-gate-structural-applicability-kpi.v1.json`) had only ever been measured "
    "against its own self-authored 42-record fixture. It enumerates the 5 OECD (2004/2007) "
    "normative requirements for (Q)SAR model validation applied to this module (2 conformant: "
    "defined endpoint, unambiguous algorithm; 1 conformant on mechanistic grounds; 2 divergent: "
    "no published applicability-domain definition and no externally-sourced validation set existed "
    "before this fire) and implements a named published applicability-domain comparator (hat-matrix "
    "leverage / Williams plot, Gramatica 2007, QSAR & Comb. Sci. 26(5):694-701, "
    "DOI 10.1002/qsar.200610151) over the fixture's 37 fact-bearing records plus the 13 T-08 "
    "held-out live-RDKit probes. Verdict: **CLAIM_REFUTED** -- 21 of 55 comparison rows (38.2%) "
    "diverge between the gate's structural pass/fail decision and the leverage-AD in/out-of-domain "
    "flag; every divergence is characterised (accelerator/hostile-null hardener declarations that "
    "are numerically in-domain but structurally rejected, and one real held-out hardener "
    "(diethyl 2-(butylamino)succinate, an aspartic-ester secondary amine) that the gate SCOREs "
    "while leverage-AD flags as an extrapolation risk) and filed to `proposed_followups[]` with a "
    "proposed repair criterion each. This does not show the gate is wrong -- the two methods answer "
    "different questions (numeric-range similarity vs mechanistic role-appropriateness) -- but it "
    "does show the module's 1.0 self-consistency figure is not equivalent to, and had never been "
    "checked against, a named published external-validation standard."
)
mission_text_new = mission_text.replace(anchor, anchor + new_bullet, 1)
assert mission_text_new != mission_text
MISSION.write_text(mission_text_new)
mission_sha_after = sha(MISSION.read_bytes())

kpi_sha = sha(KPI_PATH.read_bytes())
analysis_sha = sha(ANALYSIS_SCRIPT.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub = rev_sk.public_key().public_bytes_raw()
rev_key_id = f"phase0-internal-reviewer-{sha(rev_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust-store id"

REFUTATION_CRITERION = (
    "The gate's accept/reject decisions have never been compared against a named published "
    "applicability-domain method (only against the module's own self-authored fixture)."
)

body_obj = {
    "schema": "amphora.molecule-design-gate.wtdesigngate-ad-comparator-receipt.v1",
    "campaign_item_id": "W-T-DESIGNGATE",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "REAL_ARITHMETIC",
    "run_type": "SCIENCE_VALIDATION_THEORY_COMPARATOR",
    "module": "amphora-molecule-design-gate",
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
    "modifies_mission_prose": True,
    "modifies_mission_front_matter": False,
    "claim_under_attack": {
        "receipt_path": "amphora-molecule-design-gate/evidence/phase0/kpis/",
        "claim_text": (
            "The gate's accept/reject decisions are compared against a published applicability-"
            "domain method."
        ),
    },
    "attack_design": (
        "THEORY-DIMENSION comparator attack. Confirmed pre-fire that "
        "evidence/phase0/kpis/ contains exactly one receipt "
        "(design-gate-structural-applicability-kpi.v1.json), whose sole ground truth is the "
        "module's own self-authored 42-record fixture -- self-referential, never checked against "
        "any named published applicability-domain (AD) method. Implemented ONE such method: "
        "hat-matrix leverage / Williams plot (Gramatica 2007), using the SAME 3 numeric facts "
        "(average_molecular_weight_g_mol, oxirane_ring_count, reactive_amine_hydrogen_count) the "
        "gate itself consumes, so the comparison isolates the methodological difference (numeric-"
        "range similarity vs substructure/role rule) rather than a data difference. Training set: "
        "the fixture's 37 fact-bearing records (autoscaled z-score descriptors, intercept-"
        "augmented hat matrix, h* = 3(p+1)/n per Tropsha/Gramatica/Gombar 2003). Applied the "
        "resulting AD model to: (a) the 37 training records themselves (self-consistency check), "
        "(b) the fixture's 5 malformed-structure records (facts undefined -> not_applicable), and "
        "(c) all 13 real, cited, live-RDKit-FFI-derived molecules from the independently DSSE-"
        "signed T-08 receipt (held out of the fixture; MW recomputed deterministically from each "
        "molecule's RDKit-derived formula using standard atomic weights, since T-08 did not record "
        "MW). Every one of the 55 resulting comparison rows is given a verdict of conformant / "
        "divergent / not_applicable with the observed leverage value, h*, AD flag, and gate "
        "decision as evidence. Also enumerated the 5 OECD (2004/2007) normative requirements for "
        "(Q)SAR model validation and scored the module's conformance to each."
    ),
    "oecd_principles_2004_2007": diag["oecd_principles_2004_2007"],
    "ad_method": diag["ad_method"],
    "comparator_results": diag["comparator_results"],
    "summary": diag["summary"],
    "proposed_followups": diag["proposed_followups"],
    "headline_result": {
        "verdict": "CLAIM_REFUTED",
        "rationale": (
            "The pinned claim (that the gate's decisions ARE compared against a published AD "
            "method) was false at fire start -- no such comparator existed anywhere in the module "
            "or its evidence tree. Beyond the documentation gap itself, implementing the missing "
            "comparator surfaces substantive divergence: 21/55 (38.2%) of comparison rows disagree "
            "between the gate's structural decision and the leverage-AD in/out-of-domain flag. "
            "This does not mean the gate is chemically wrong on any of these 21 cases (all 21 "
            "gate decisions independently match either the fixture's hand-derived expected labels "
            "or T-08's live-RDKit-verified expected status) -- it means the module's internal 1.0 "
            "self-consistency figure is not, and had never been shown to be, equivalent to "
            "agreement with an external, named, published validation standard. That gap is the "
            "refutation."
        ),
    },
    "refutation_criterion_registry": {
        "criterion": REFUTATION_CRITERION,
        "observed": (
            f"Confirmed TRUE pre-fire: {KPI_PATH.name} (sha256 {kpi_sha}) is the module's only "
            "phase0/kpis receipt and its authority/ground-truth is exclusively the self-authored "
            "fixture; grep of the module tree found no other AD-method receipt. The named "
            "observation (no comparison against a published AD method exists) DID occur, "
            "confirming the refutation. This fire's own new comparator receipt is the first such "
            "comparison and is not itself a repair of the gate -- it is the missing measurement."
        ),
    },
    "does_not_close": [
        "Does not establish that the gate is chemically incorrect on any case; all 55 gate "
        "decisions independently verified elsewhere (fixture hand-labels or T-08 live-RDKit "
        "probes) remain unchanged and uncontested by this fire.",
        "Does not modify design_gate_result, the fixture, module-manifest.json, or any signed "
        "Phase-0 KPI receipt.",
        "Does not implement the second named AD method (Tanimoto-distance / nearest-neighbor "
        "fingerprint AD, Sheridan et al. 2004) the campaign item also permits; only leverage/"
        "Williams-plot was implemented. A cross-method agreement check between the two named AD "
        "methods themselves is future work.",
        "Does not resolve the OECD-P3/P4 divergences it documents -- see proposed_followups[] for "
        "the two structural repair candidates (surfacing an explicit applicability_domain_flag on "
        "SCORED decisions; documenting in mission.md that AD in-domain status is not a proxy for "
        "role-appropriateness).",
        "Does not touch mission.md front matter (phase/readiness) or the master manifest.",
    ],
    "provenance": {
        "analysis_script_path": "evidence/phase0/repairs/W-T-DESIGNGATE/work/wtdg_analysis.py",
        "analysis_script_sha256": analysis_sha,
        "fixture_sha256": diag["provenance"]["fixture_sha256"],
        "t08_receipt_sha256": diag["provenance"]["t08_receipt_sha256"],
        "kpi_receipt_sha256_at_fire_start": kpi_sha,
        "mission_md_sha256_before": mission_sha_before,
        "mission_md_sha256_after": mission_sha_after,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "diagnostic_byte_identical": canon == runB,
        "determinism_basis": (
            "no RNG, no wall-clock; fixed hardcoded fixture/T-08-receipt inputs; plain "
            "Gauss-Jordan linear algebra (no numpy/BLAS thread nondeterminism); deterministic "
            "sort_keys JSON serialization."
        ),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub.hex(),
        "used_for": "AUDIT_ONLY theory-comparator receipt under evidence/phase0/repairs/W-T-DESIGNGATE/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub.hex(),
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-design-gate-wtdesigngate-ad-comparator+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub.hex(),
    "reviewer_public_key_hex": rev_pub.hex(),
    "signature": envelope,
}
out = ITEM / "done" / "w-t-designgate-ad-comparator-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_diag_sha256", diag_sha)
print("analysis_script_sha256", analysis_sha)
print("mission_sha_before", mission_sha_before)
print("mission_sha_after", mission_sha_after)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
print("verdict", "CLAIM_REFUTED")
print("n_total", summary["n_total"], "n_divergent", summary["n_divergent"], "n_conformant", summary["n_conformant"], "n_na", summary["n_not_applicable"])
