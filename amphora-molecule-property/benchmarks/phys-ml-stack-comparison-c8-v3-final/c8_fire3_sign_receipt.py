#!/usr/bin/env python3
"""C8 fire 3 of 4: FINAL consolidated per-property {physics, ML, stack} receipt.

Reconciles fire 1 (built all four property triplets; found RadonPy dielectric
ground-truth label defect) and fire 2 (escalated the dielectric finding to a
zero-contamination retrain, decisively showing NO arm -- physics, ML, or stack
-- beats a mean baseline on the physically-valid 10.5% dielectric subset).

This receipt is the deliverable the C8 done_criterion asks for: ONE
consolidated signed receipt covering density, Tg (with stack arm), dielectric,
and refractive index. It does not re-run any computation; it cites fire 1 and
fire 2 by sha256 and re-emits their numbers into one table, with the
dielectric row REWRITTEN from fire 1's naive positive-looking triplet to
fire 2's honest "no competent model" finding. This makes the founder-facing F8
panel buildable with zero fabricated/misleading numbers: 3 real triplets +
1 explicit, quantified negative result -- which is itself receipt-backed and
not a placeholder.
"""
import json, base64, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-property/benchmarks"
FIRE1_DIR = BENCH / "phys-ml-stack-comparison-c8-v1"
FIRE2_DIR = BENCH / "phys-ml-stack-comparison-c8-fire2-clean-subset-v1"
OUT = BENCH / "phys-ml-stack-comparison-c8-v3-final"
OUT.mkdir(parents=True, exist_ok=True)
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

fire1 = json.loads((FIRE1_DIR / "c8_phys_ml_stack_comparison_receipt.v1.json").read_text())
fire2 = json.loads((FIRE2_DIR / "c8_fire2_dielectric_clean_subset_receipt.v1.json").read_text())


def sha_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


FIRE1_SHA = sha_file(FIRE1_DIR / "c8_phys_ml_stack_comparison_receipt.v1.json")
FIRE2_SHA = sha_file(FIRE2_DIR / "c8_fire2_dielectric_clean_subset_receipt.v1.json")

p1 = fire1["per_property_comparison"]


def build_receipt():
    final_comparison = {
        "density": p1["density"],
        "tg": p1["tg"],
        "refractive_index": p1["refractive_index"],
        "dielectric_constant": {
            "population": p1["dielectric"]["population"],
            "split_contaminated_population_fire1": p1["dielectric"]["split"],
            "split_clean_only_fire2": fire2["split"],
            "label_integrity_finding": {
                "test": "eps_static >= eps_infinity = n_measured^2 (Frohlich 1949 Ch.2 / Debye 1929, model-independent thermodynamic inequality)",
                "violation_rate": "962/1075 = 89.5% of RadonPy PI1070 static_dielectric_const rows",
                "openpoly_control": "0/295 violations in OpenPoly's own internally-consistent DFT decomposition (eps_Total>=eps_Electronic) -- isolates the defect to RadonPy's MD fluctuation-formula route",
                "source_receipt_sha256": FIRE1_SHA,
            },
            "contaminated_population_numbers_NOT_CITABLE": {
                "note": "Reported for audit-trail completeness only. Trained/evaluated on the 89.5%-corrupted population (or a clean test slice of a model still trained on it). DO NOT cite in the F8 founder panel -- see verdict below.",
                "physics_full_population": {"MAE": p1["dielectric"]["physics"]["full_population_test_MAE"], "R2": p1["dielectric"]["physics"]["full_population_test_R2"]},
                "ml_full_population": {"MAE": p1["dielectric"]["ml"]["full_population_test_MAE"], "R2": p1["dielectric"]["ml"]["full_population_test_R2"]},
                "ml_shipped_kpi_radonpy_slice": p1["dielectric"]["ml"]["existing_shipped_KPI_for_context"],
                "stack_full_population": {"MAE": p1["dielectric"]["stack"]["full_population_test_MAE"], "R2": p1["dielectric"]["stack"]["full_population_test_R2"]},
            },
            "clean_only_zero_contamination_pipeline_CITABLE": {
                "note": "RF and stack meta-learner retrained FROM SCRATCH on ONLY the 113/1075=10.5% physically-valid rows (train+calib+test alike). This is the honest number.",
                "n_train": 67, "n_calib": 22, "n_test": 24,
                "physics": fire2["results"]["physics_clean_only"],
                "ml": fire2["results"]["ml_clean_only"],
                "stack": fire2["results"]["stack_clean_only"],
                "paired_bootstrap_physics_minus_ml_mae_ci90": fire2["results"]["paired_bootstrap_physics_minus_ml_mae"],
                "source_receipt_sha256": FIRE2_SHA,
            },
            "openpoly_physics_arm": p1["dielectric"]["openpoly_dielectric_physics_arm"],
            "verdict": "NO_COMPETENT_MODEL -- all three of {physics, ML, stack} score R2<=0 (worse than the test-set mean) on the physically-valid clean-only subset (n=113 total, n_test=24); the paired bootstrap 90% CI of physics-minus-ML MAE advantage includes zero. The dielectric row of the F8 founder panel MUST read 'NO COMPETENT MODEL -- label integrity failure, n_clean=113' and MUST NOT cite the contaminated-population R2=0.64 ML number.",
        },
    }
    return {
        "schema": "amphora.molecule-property.c8-phys-ml-stack-comparison-receipt.v1",
        "receipt_id": "c8-fire3-final-consolidated-comparison",
        "study_id": "c8-phys-ml-stack-comparison",
        "campaign_item_id": "C8",
        "fire_sequence": "C8 fire 3 of 4 (max_fires). FINAL consolidated deliverable superseding fire 1's naive dielectric row.",
        "authority": "AUDIT_ONLY",
        "promotes_nothing": True,
        "modifies_no_live_config": True,
        "module": "amphora-molecule-property",
        "claim_under_attack": {
            "receipt_path": "amphora-molecule-property/evidence/phase0/kpis/radonpy-density-ml-vs-van-krevelen-physics-kpi.v1.json",
            "claim_text": "A founder-facing per-property physics-vs-ML-vs-stack comparison can be built entirely from receipt-backed numbers (no illustrative placeholders).",
        },
        "prior_fire_context": (
            "Fire 1 (sha256=" + FIRE1_SHA + ") built all four property triplets and, while building the "
            "dielectric physics arm, found RadonPy PI1070's static_dielectric_const ground-truth label "
            "violates a model-independent thermodynamic inequality in 89.5% of rows. Fire 1's own probe "
            "was weak (RF trained on the full corrupted population, only test-sliced to clean rows). "
            "Fire 2 (sha256=" + FIRE2_SHA + ") escalated to a zero-contamination pipeline -- RF and stack "
            "retrained from scratch on ONLY the 10.5% physically-valid rows -- and found all three arms "
            "(physics, ML, stack) score R2<=0 on honest data, with the physics-vs-ML MAE gap's bootstrap "
            "CI including zero. Fire 2's recommended followup: 'produce the formal dielectric: no "
            "competent model F8 table row text so the campaign item can close honestly.' This fire does "
            "exactly that -- it is a reconciliation and consolidation fire, not a new experiment."
        ),
        "objective": (
            "Emit the ONE consolidated, DSSE-signed, founder-report-citable per-property phys/ML/stack "
            "comparison receipt that the C8 done_criterion requires: density, Tg (with stack arm), "
            "dielectric, refractive index. Density/Tg/RI carry forward fire 1's triplets verbatim "
            "(cited by sha256, not recomputed). Dielectric is REWRITTEN to replace fire 1's "
            "naive-looking positive numbers with fire 2's honest zero-contamination finding: NO "
            "COMPETENT MODEL on the physically valid subset. This is the table this campaign item set "
            "out to build -- it satisfies 'no illustrative placeholders' by replacing the one property "
            "that cannot honestly get a positive triplet with an explicit, quantified, receipt-backed "
            "negative result instead of silently omitting it or citing a corrupted-label number."
        ),
        "verdict": "CLAIM_REFUTED",
        "verdict_rationale": (
            "The claim under attack asserts a founder-facing comparison table can be built ENTIRELY from "
            "receipt-backed numbers with no illustrative placeholders. 3 of 4 properties (density, Tg, "
            "refractive index) support real, receipt-backed {physics, ML, stack} triplets -- that part of "
            "the claim SURVIVES. But the claim's implicit premise -- that every property cell in such a "
            "table can be filled with a competent positive point estimate -- is REFUTED for dielectric "
            "constant: no {physics, ML, stack} arm beats a mean baseline on physically-valid data, and "
            "the number the shipped KPI would otherwise supply (R2=0.64) is an artifact of a corrupted, "
            "low-variance majority label, not real skill. A table built by (mis)citing that number to "
            "fill the dielectric cell would BE an illustrative placeholder wearing a receipt's clothing. "
            "The only receipt-backed way to fill that cell honestly is the negative result recorded here."
        ),
        "per_property_comparison": final_comparison,
        "founder_f8_panel_row_text": {
            "density": "Physics (Van Krevelen) MAE 0.1327 g/cm3 -> ML (RF) MAE 0.0566 -> Stack MAE 0.0569 g/cm3 (RadonPy PI1070, n_test=216)",
            "tg": "Physics (VK Ridge Y_gi, external) MAE 70.42 K -> ML (RF LOSO) MAE 51.24 K [fresh-split ML 48.77 K] -> Stack MAE 54.05 K (OpenPoly, n_test=89)",
            "refractive_index": "Physics (Lorentz-Lorenz) MAE 0.0377 -> ML (RF) MAE 0.0303 [mixed] / 0.0253 [RadonPy-comparable] -> Stack MAE 0.0276 (RadonPy-only physics/stack, n_test=211; ML mixed n_test=246)",
            "dielectric_constant": "NO COMPETENT MODEL -- label integrity failure (89.5% of RadonPy ground-truth violates eps_static>=n^2); on the n=113 physically-valid subset all of {physics MAE 19.9 R2 -1.04, ML MAE 13.1 R2 -0.03, stack MAE 14.5 R2 -0.05} fail to beat the test-set mean. Do not report a point estimate.",
        },
        "gates": {
            "two_replay_byte_stable_this_receipt": None,
            "no_new_computation_pure_reconciliation": True,
            "fire1_and_fire2_cited_by_sha256_not_recomputed": True,
            "dielectric_row_no_longer_cites_contaminated_population_number": True,
            "density_tg_ri_arms_carried_forward_verbatim": True,
            "signature_field_is_dsse_envelope_object": True,
        },
        "all_gates_passed": True,
        "rights_check": "No new source touched; pure reconciliation of two already rights-cleared prior fires in this module. No quarantined/CONTEXT_ONLY source opened.",
        "ceiling": (
            "AUDIT_ONLY red-team comparison-table construction + falsification receipt. This is the FINAL "
            "consolidated artifact for C8: it is the receipt a founder-report generator should cite for "
            "the F8 panel. Does not itself alter any shipped KPI receipt, module honesty ceiling, "
            "manifest, or authority ceiling."
        ),
        "promotion_blocked_by": "NOT this audit's science (all gates pass) and NOT key custody. Manifest untouched at 66/11.",
        "openpoly_physics_gaps_filed_to_data_ask_queue": fire1.get("openpoly_physics_gaps_filed_to_data_ask_queue"),
        "recommended_followups": [
            "campaign_item C8 done_criterion met: one consolidated signed phys/ML/stack receipt now covers all four properties (3 positive triplets + 1 quantified negative result). Recommend campaign_item_status=done.",
            "Future work (not required for C8 closure): if the queued RadonPy dielectric data-integrity ask (filed fire 1, data-acquisition-queue.jsonl) is ever resolved with a re-converged or experimental corpus, re-run this dielectric arm and supersede this receipt.",
            "OpenPoly physics arms for dielectric and refractive index remain BLOCKED_DATA (no density/dipole source in this module) -- unchanged from fire 1, already queued.",
            "Any founder report generator citing this table MUST use the dielectric_constant.verdict field and founder_f8_panel_row_text.dielectric_constant string verbatim; it must not fall back to the contaminated_population_numbers_NOT_CITABLE block.",
        ],
        "signing_key": {
            "key_id": PUB["key_id"],
            "authority": PUB["authority"],
            "public_key_hex": PUB["public_key_hex"],
            "trust_anchored": False,
            "note": "NOT in config/phase0-trust-store.v1.json; audit evidence only",
        },
    }


r1 = build_receipt()
r2 = build_receipt()
body1 = json.dumps(r1, indent=2, sort_keys=True).encode()
body2 = json.dumps(r2, indent=2, sort_keys=True).encode()
assert body1 == body2, "this receipt's own content is non-deterministic"
(OUT / "receipt_body.canonical.json").write_bytes(body1)
(OUT / "receipt_body.runB.json").write_bytes(body2)

receipt = build_receipt()
receipt["gates"]["two_replay_byte_stable_this_receipt"] = True
receipt["two_replay_gate"] = {
    "canonical_sha256": sha(body1),
    "runB_sha256": sha(body2),
    "byte_identical": body1 == body2,
}

body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-property.c8-phys-ml-stack-comparison-receipt.v1+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}],
}

out = dict(receipt)
out["signature"] = envelope

outpath = OUT / "c8_fire3_final_consolidated_receipt.v1.json"
outpath.write_text(json.dumps(out, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUB["public_key_hex"])).verify(sig, pae(ptype, body))
assert isinstance(json.loads(outpath.read_text())["signature"], dict), "signature must serialize as JSON object"

print("SIGNED_OK", outpath)
print("receipt_id", receipt["receipt_id"])
print("sig_verified True")
print("signature_type", type(json.loads(outpath.read_text())["signature"]).__name__)
