#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-NOV1 done receipt for amphora-molecule-novelty.
Construction replicates the module's own R-A07/V-A07/R-A07v2 signers exactly:
pae(), load_seed(), payloadType style, envelope fields, attestation keys.

W-NOV1 closes campaign item W-NOV1 by independently re-attacking the orphaned
R-A07v2 superseding repair (computed 2026-08-04, correctly documented in
RETRACTION-INDEX.md, but never logged to the falsification ledger nor published
under a campaign path, so the campaign item's done_check could not see it).
This receipt does not modify R-A07v2 or any other existing signed artifact.
"""
import base64
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-novelty"
ITEM = MOD / "evidence/phase0/repairs/W-NOV1"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

R_A07V2_DONE = "amphora-molecule-novelty/evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json"

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

canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["checks_all_pass"] is True
harness_sha = sha((WORK / "run_wnov1_verify.py").read_bytes())

r_a07v2_sha_now = sha((ROOT / R_A07V2_DONE).read_bytes())
assert r_a07v2_sha_now == diag["r_a07v2_sha256"], "R-A07v2 changed since verification ran"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
assert eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"), "evaluator key not anchored in phase0 trust store"

body_obj = {
    "schema": "amphora.module-repair-done.v1",
    "receipt_id": "w-nov1-done-receipt-v1",
    "module_id": "amphora-molecule-novelty",
    "campaign_item_id": "W-NOV1",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "date": "2026-08-05",
    "generated_on_host": "xbabe2",
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_mission_front_matter": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "trust_anchored_in_phase0_store": True,
    "appends_to_falsification_ledger": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,

    "claim": (
        "The Phase-0 novelty KPI's per-family conformal table "
        "(evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json) "
        "is derived from the CAS-correct isophorone diamine (IPDA) structure "
        "(CAS 2855-13-2, C10H22N2) in every one of its four fingerprint families "
        "(morgan_r2_2048, maccs_166, atompair_2048, toptorsion_2048), not just morgan_r2_2048, "
        "computed on the canonically-deduplicated 350-structure OpenPoly corpus, with every "
        "structural-correction flip disclosed -- the specific claim campaign item W-NOV1 targets."
    ),
    "background": (
        "V-A07 (2026-08-04, verdict CLAIM_REFUTED) established that R-A07's shipped four-family "
        "table applied the IPDA structural correction only inside a separate morgan_r2_2048-only "
        "side table, leaving maccs_166 / atompair_2048 / toptorsion_2048 computed on the refuted "
        "C9H20N2 string, and surfaced one undisclosed flip (atompair_2048 / IPDA / alpha=0.01, "
        "conformal p 0.011396 -> 0.008547, NOVEL false -> true) when the correction was actually "
        "propagated. A follow-up repair, R-A07v2, was computed and DSSE-signed on 2026-08-04 "
        "(evidence/phase0/repairs/R-A07v2/done/...), fully propagating the corrected structure "
        "into all four families, disclosing that flip alongside R-A07's original 5 dedup-only "
        "flips, and documenting the whole chain in RETRACTION-INDEX.md. That fire never appended "
        "a falisification-ledger line and never published under a campaign item path, so it was "
        "orphaned: campaign item W-NOV1 was created to close exactly this gap, and its done_check "
        "(a signed receipt under evidence/phase0/repairs/W-NOV1/done/) could not see R-A07v2's "
        "existing, correct work sitting under a different item's path."
    ),
    "action_taken": (
        "Did not recompute or re-sign R-A07v2 (supersede-never-rewrite; nothing about it is wrong). "
        "Instead, independently re-attacked it per repair-mode rule 2, from scratch: (1) verified "
        "R-A07v2's DSSE envelope against the pinned Phase-0 evaluator key read fresh from the trust "
        "store; (2) verified byte-intactness of the whole supersession chain (KPI, R-A07, V-A07, "
        "R-A07v2, dedup + identity audit receipts, genmod ground truth); (3) re-derived isophorone "
        "diamine a FIFTH independent way (CC1(C)CC(CN)(C)CC(N)C1, from the gem-dimethyl carbon going "
        "the ring-traversal direction opposite every prior derivation) and confirmed C10H22N2 / "
        "one six-membered ring / two primary amine N / three methyl C and canonical-SMILES identity "
        "with R-A07v2's own re-derivation; (4) reimplemented the entire four-family conformal table "
        "on the deduplicated 350-structure corpus from fresh RDKit featurization code (not copied "
        "from run_ra07v2.py) and diffed all 20 published cells against R-A07v2's shipped table."
    ),
    "finding": {
        "genuinely_falsifying_observation_sought": (
            "Any of the 20 shipped (family, candidate) NN-Tanimoto, conformal-p or novel_by_alpha "
            "values failing to reproduce under independent fresh reimplementation; the DSSE "
            "signature failing to verify against the pinned key; or the atompair_2048/IPDA/alpha=0.01 "
            "flip (the specific undisclosed defect V-A07 found) failing to reproduce."
        ),
        "self_correcting_near_miss": (
            "The first independent reimplementation DID initially disagree on 2 of 20 cells "
            "(DDS/morgan_r2_2048, DDS/toptorsion_2048: conformal_p differed in the 3rd-4th "
            "decimal, though novel_by_alpha verdicts still matched). Root-caused to a bug in "
            "THIS re-verification's own leave-one-out code: it excluded the self point by "
            "display Name rather than corpus index. The 350 canonically-distinct structures "
            "contain 6 duplicate-name groups (chitosan, cellulose, polyimide, starch, "
            "polylactide, poly(alpha-methylstyrene) each appear twice as two genuinely "
            "distinct canonical structures), so name-based exclusion wrongly dropped a valid "
            "same-named-but-distinct neighbour from 2 leave-one-out calibration sets. Fixed to "
            "index-based exclusion (matching R-A07v2's own calib_alphas, which was already "
            "index-based and therefore correct); after the fix all 20 cells reproduce exactly."
        ),
        "n_cells_compared": diag["checks"]["5a_n_cells_compared"],
        "n_cells_reproduced_exactly": diag["checks"]["5b_n_cells_matching_shipped_r_a07v2_table"],
        "all_20_cells_reproduce_after_fix": diag["checks"]["5c_all_20_cells_reproduce_exactly"],
        "dsse_signature_independently_verifies": diag["checks"]["1c_r_a07v2_dsse_signature_verifies_against_pinned_key"],
        "atompair_ipda_a01_flip_reproduced": diag["checks"]["6a_atompair_ipda_a01_novel_true_reproduced"],
        "headline_5_of_5_novel_reproduced": diag["checks"]["7a_all_5_below_0_40_fixed_cutoff"],
        "morgan_ipda_nn_unchanged_by_structural_fix_reproduced": diag["checks"]["7b_morgan_ipda_nn_unchanged_by_structural_fix"],
        "duplicate_display_name_groups_found_among_350_distinct_structures": diag["duplicate_display_name_groups_among_350_distinct_structures"],
    },
    "verdict": "CLAIM_SURVIVED",
    "verdict_statement": (
        "The claim under attack -- that the KPI's per-family table is correctly derived from "
        "the CAS-correct IPDA structure in ALL FOUR fingerprint families, on the deduplicated "
        "350-structure corpus, with every flip disclosed -- SURVIVES independent re-attack. "
        "R-A07v2 (evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-"
        "repair-receipt.v1.dsse.json, sha256 " + diag["r_a07v2_sha256"] + ") already fully "
        "discharges campaign item W-NOV1's objective: it propagates the corrected structure "
        "into every family, discloses the atompair_2048/IPDA/alpha=0.01 flip V-A07 surfaced "
        "alongside R-A07's 5 dedup-only flips, and explicitly states the top-level 5/5-NOVEL "
        "headline stands. This receipt formally closes W-NOV1 by publishing that independent "
        "confirmation under the campaign item's own path; R-A07v2 itself is left byte-intact."
    ),
    "top_level_5_of_5_novel_headline_stands": True,
    "checks": diag["checks"],
    "checks_all_pass": diag["checks_all_pass"],
    "r_a07v2_receipt_path": R_A07V2_DONE,
    "r_a07v2_receipt_sha256": diag["r_a07v2_sha256"],
    "kpi_receipt_sha256_unchanged": diag["kpi_sha256"],
    "ipda_independent_rederivation_smiles": diag["ipda_independent_rederivation_smiles"],
    "ipda_independent_rederivation_canonical": diag["ipda_independent_rederivation_canonical"],
    "ipda_independent_rederivation_formula": diag["ipda_independent_rederivation_formula"],
    "dedup_set_sha256": diag["dedup_set_sha256"],
    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, qualification, regulatory or "
        "FTO authority. AUDIT_ONLY, ceiling EVIDENCE_ONLY.",
        "Does not create a new supersession: R-A07v2 remains the operative superseding artifact "
        "for R-A07; this receipt only independently re-verifies it and closes the campaign item "
        "that tracks that work.",
        "Does not re-litigate corpus exchangeability beyond the dedup already performed and "
        "verified in prior receipts.",
    ],
    "theory_reference": (
        "Vovk, Gammerman & Shafer 2005 Algorithmic Learning in a Random World (split conformal "
        "prediction); Bajusz, Racz & Heberger 2015 J. Cheminform. 7:20 (Tanimoto coefficient "
        "interpretation); Rogers & Hahn 2010 J. Chem. Inf. Model. 50(5):742-754 (Morgan/ECFP); "
        "RDKit MACCS keys, atom-pair and topological-torsion fingerprints; Lee & Neville 1967 "
        "Handbook of Epoxy Resins (isophorone diamine constitution, CAS 2855-13-2)."
    ),
    "rdkit_version": "2026.03.2",
    "reproducibility": {
        "byte_identical": canon == runB,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "harness_sha256": {"run_wnov1_verify.py": harness_sha},
        "replay_method": (
            "run_wnov1_verify.py executed twice with distinct output filenames "
            "(diagnostic.canonical.json, diagnostic.runB.json); payload serialized with "
            "json.dumps(sort_keys=True) each run and asserted byte-equal before signing."
        ),
        "two_replay_sha256_gate": "PASS",
    },
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "used_for": "AUDIT_ONLY done receipt under evidence/phase0/repairs/W-NOV1/done/",
        "derives_pinned_trust_store_key_id": True,
        "signs_phase0_evaluation_or_review": False,
    },
}
body = json.dumps(body_obj, sort_keys=True).encode()
payload_b64 = base64.b64encode(body).decode()
payload_type = "application/vnd.amphora.molecule-novelty-w-nov1-done+json"
sig = eval_sk.sign(pae(payload_type, body))
sig_b64 = base64.b64encode(sig).decode()

envelope = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": {
        "payloadType": payload_type,
        "payload": payload_b64,
        "signatures": [{"keyid": eval_key_id, "sig": sig_b64}],
    },
}

pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
pub.verify(sig, pae(payload_type, body))

DONE.mkdir(parents=True, exist_ok=True)
out_path = DONE / "w-nov1-done-receipt.v1.dsse.json"
out_path.write_text(json.dumps(envelope, indent=2))
print("WROTE", out_path)
print("verdict:", body_obj["verdict"])
print("self_verify_ok: True")
print("sha256:", sha(out_path.read_bytes()))
