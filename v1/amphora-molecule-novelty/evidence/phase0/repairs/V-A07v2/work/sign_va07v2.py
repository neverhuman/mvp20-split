#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V-A07v2 done receipt for amphora-molecule-novelty.
Construction replicates the module's own R-A07/V-A07/R-A07v2/W-NOV1 signers:
pae(), load_seed(), payloadType style, envelope fields, attestation keys.

V-A07v2 independently verifies R-A07v2 (the four-family IPDA propagation
repair) and W-NOV1 (the prior independent verify of it, which landed first,
2026-08-05, CLAIM_SURVIVED). Does not modify either.
"""
import base64
import hashlib
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-novelty"
ITEM = MOD / "evidence/phase0/repairs/V-A07v2"
WORK = ITEM / "work"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

R_A07V2_DONE = "amphora-molecule-novelty/evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json"
W_NOV1_DONE = "amphora-molecule-novelty/evidence/phase0/repairs/W-NOV1/done/w-nov1-done-receipt.v1.dsse.json"

DIRECTIVE_PATH = "docs/directives/2026-08-05-closing-the-open-portfolio.md"
DIRECTIVE_SHA256 = "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d"


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
harness_sha = sha((WORK / "run_va07v2_verify.py").read_bytes())

r_a07v2_sha_now = sha((ROOT / R_A07V2_DONE).read_bytes())
w_nov1_sha_now = sha((ROOT / W_NOV1_DONE).read_bytes())
assert r_a07v2_sha_now == diag["r_a07v2_sha256"], "R-A07v2 changed since verification ran"
assert w_nov1_sha_now == diag["w_nov1_sha256"], "W-NOV1 changed since verification ran"

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
assert eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"), "evaluator key not anchored in phase0 trust store"

body_obj = {
    "schema": "amphora.module-repair-done.v1",
    "receipt_id": "v-a07v2-done-receipt-v1",
    "module_id": "amphora-molecule-novelty",
    "campaign_item_id": "V-A07v2",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "date": "2026-08-11",
    "generated_on_host": "xbabe2",
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_mission_front_matter": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "trust_anchored_in_phase0_store": True,
    "appends_to_falsification_ledger": True,
    "human_review_performed": False,
    "organizational_independence_asserted": False,

    "directive_path": DIRECTIVE_PATH,
    "directive_sha256": DIRECTIVE_SHA256,
    "directive_obligation": "V2-A07v2",

    "claim": (
        "The Phase-0 novelty KPI's per-family conformal table "
        "(evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json) "
        "is derived from the CAS-correct isophorone diamine (IPDA) structure "
        "(CAS 2855-13-2, C10H22N2) in every one of its four fingerprint families "
        "(morgan_r2_2048, maccs_166, atompair_2048, toptorsion_2048), not just morgan_r2_2048, "
        "computed on the canonically-deduplicated 350-structure OpenPoly corpus, with every "
        "structural-correction flip disclosed -- as repaired by R-A07v2 "
        "(evidence/phase0/repairs/R-A07v2/done/...) and independently verified once already by "
        "W-NOV1 (evidence/phase0/repairs/W-NOV1/done/..., 2026-08-05, CLAIM_SURVIVED)."
    ),
    "refutation_criterion_verbatim": (
        "Independently recompute the nearest-neighbour Tanimoto for all five candidates in ALL "
        "FOUR fingerprint families on the deduplicated corpus; confirm every disclosed flip and "
        "hunt for any UNdisclosed one. A single undisclosed cell flip = CLAIM_REFUTED."
    ),
    "refutation_criterion_observation": (
        "NOT OBSERVED as stated: zero undisclosed cell flips found across all 20 (family, "
        "candidate) cells in a sixth independent reimplementation, diffed against R-A07v2's "
        "shipped table to <1e-9 on both nn_tanimoto and conformal_p, with identical "
        "novel_by_alpha verdicts at every alpha. The single disclosed flip "
        "(atompair_2048/IPDA/alpha=0.01, NOVEL false->true) independently reproduces. HOWEVER, "
        "a genuinely falsifying observation of a DIFFERENT, adjacent kind WAS found and is "
        "disclosed in full below: the corpus's 'canonically-distinct 350' label is factually "
        "wrong (348 truly distinct repeat-unit structures; 2 undisclosed duplicate structure "
        "pairs survive RDKit canonical-SMILES dedup due to an atom-mapped-wildcard notation bug "
        "in the shared cap() convention used by every receipt in this chain). This is an "
        "exchangeability-precondition violation, not a cell flip in the sense the criterion "
        "names, and a materiality re-derivation on the truthful 348-structure corpus confirms it "
        "changes zero of the 20 published verdicts -- so it does not meet the item's literal "
        "refutation bar, and CLAIM_SURVIVED is reported honestly rather than silently reported "
        "as a clean pass. See corpus_exchangeability_defect_found below for full disclosure."
    ),

    "background": (
        "W-NOV1 (2026-08-05, verdict CLAIM_SURVIVED) already independently verified R-A07v2 with "
        "a fifth independent IPDA re-derivation and a fresh reimplementation of the full 20-cell "
        "table, reproducing all 20 cells exactly. Per this item's objective ('INDEPENDENT VERIFY "
        "of R-A07v2, and of W-NOV1 if that landed first'), this fire treats W-NOV1 as already "
        "landed and mounts a SIXTH independent attack using an attack surface none of the five "
        "prior fires in this claim chain (R-A07, V-A07, R-A07v2, W-NOV1, and the original "
        "corpus-duplicate-exchangeability-audit-v1) used: the corpus dedup that every one of "
        "them relies on and calls 'structure-only, label-free' uses RDKit canonical-SMILES-"
        "string equality exclusively. Canonical SMILES is NOT a normalized structure "
        "representation for tautomers or for atom-mapped notation variants of the same repeat "
        "unit, so it is possible for the '350 canonically-distinct' corpus to still contain "
        "undisclosed duplicates that an independent structural-identity method (InChIKey) would "
        "catch."
    ),
    "action_taken": (
        "(1) Independently re-verified R-A07v2's and W-NOV1's DSSE envelopes against the pinned "
        "Phase-0 evaluator key read fresh from the trust store; byte-locked both done receipts. "
        "(2) Re-derived isophorone diamine a SIXTH independent way "
        "(C1C(C)(C)CC(N)CC1(C)CN, starting from the ring CH2 between the gem-dimethyl carbon and "
        "the quaternary carbon -- distinct from all five prior derivation strings) and confirmed "
        "C10H22N2 / one six-membered ring / two primary amine N / three methyl C and "
        "canonical-SMILES identity with R-A07v2's, W-NOV1's, and the amphora-molecule-generator "
        "known_answer_amines ground-truth structures. (3) Reimplemented the entire four-family "
        "conformal table on the deduplicated 350-structure corpus from fresh RDKit featurization "
        "code (not copied from run_ra07v2.py or run_wnov1_verify.py) and diffed all 20 published "
        "cells against R-A07v2's shipped table -- zero undisclosed flips. (4) NEW: computed an "
        "InChIKey for every one of the 350 'canonically distinct' corpus structures and grouped "
        "by key, finding 2 undisclosed duplicate structure pairs RDKit canonical-SMILES dedup "
        "missed; traced the root cause to the shared cap() convention's failure to normalize "
        "atom-mapped wildcard notation; rebuilt the table on the truthful 348-structure corpus "
        "and confirmed the defect changes zero of the 20 published verdicts (materiality check). "
        "(5) Positive control: planted a genuine lactam/lactim tautomer duplicate pair "
        "(2-piperidone / its lactim tautomer) into a copy of the corpus, distinct in RDKit "
        "canonical SMILES but identical in InChIKey, and confirmed the InChIKey-collision "
        "detector correctly fires on it."
    ),

    "sixth_independent_ipda_rederivation": diag["ipda_sixth_rederivation"],
    "twenty_cell_table_verification": {
        "n_cells_compared": diag["checks"]["7a_n_cells_compared"],
        "n_cells_matching_shipped": diag["checks"]["7b_n_cells_matching_shipped_r_a07v2"],
        "all_20_cells_reproduce_exactly": diag["checks"]["7c_all_20_cells_reproduce_exactly"],
        "n_undisclosed_flips_found": diag["n_undisclosed_flips_found"],
        "atompair_ipda_a01_disclosed_flip_reproduced": diag["checks"]["8a_atompair_ipda_a01_novel_true_reproduced"],
        "morgan_ipda_nn_unchanged_by_structural_fix_reproduced": diag["checks"]["8b_morgan_ipda_nn_unchanged_by_structural_fix"],
        "top_level_5_of_5_novel_reproduced": diag["checks"]["9a_top_level_five_of_five_novel"],
    },
    "flip_completeness_verdict": diag["flip_completeness_verdict"],

    "corpus_exchangeability_defect_found": {
        "summary": (
            "The '350 canonically-distinct' OpenPoly calibration corpus, which every receipt in "
            "this claim chain (R-A07, V-A07, R-A07v2, W-NOV1) and the standalone "
            "corpus-duplicate-exchangeability-audit-v1 (2026-08-02) treats as duplicate-free, "
            "actually contains 348 truly distinct repeat-unit structures, not 350: 2 pairs of "
            "rows describe the identical polymer repeat unit under two different display names "
            "and two different PSMILES end-group notations, and RDKit canonical-SMILES-string "
            "dedup (the only method ever applied) cannot see this because it does not normalize "
            "atom-mapped wildcard notation."
        ),
        "n_undisclosed_duplicate_groups": diag["inchikey_audit"]["n_undisclosed_duplicate_groups_found"],
        "undisclosed_duplicate_groups": diag["inchikey_audit"]["undisclosed_duplicate_groups"],
        "root_cause": diag["inchikey_audit"]["root_cause"],
        "materiality_check": diag["inchikey_audit"]["materiality_check"],
        "disposition": (
            "Disclosed here in full per falsification-first obligations. Not escalated to "
            "CLAIM_REFUTED because it is outside the specific refutation criterion this campaign "
            "item pins (cell flips in the four-family table) and materiality re-derivation shows "
            "it changes zero published verdicts. This IS a genuine, previously-undisclosed defect "
            "in the corpus construction shared by every receipt in the amphora-molecule-novelty "
            "IPDA chain, and a natural target for a future ROTATION-mode attack on "
            "corpus-duplicate-exchangeability-audit-v1 or a dedicated repair item (fix cap() to "
            "strip atom-map annotations before canonicalization, re-lock the dedup set hash)."
        ),
    },

    "positive_control": diag["positive_control"],

    "verdict": "CLAIM_SURVIVED",
    "verdict_statement": (
        "The claim under attack -- that R-A07v2's four-family conformal table (independently "
        "re-verified once already by W-NOV1) is correctly derived from the CAS-correct IPDA "
        "structure in ALL FOUR fingerprint families, on the deduplicated corpus, with every flip "
        "disclosed -- SURVIVES this sixth independent re-attack. Zero undisclosed cell flips were "
        "found across 20 independently recomputed cells; the disclosed atompair_2048/IPDA/"
        "alpha=0.01 flip reproduces; the 5/5-NOVEL headline reproduces. A positive control "
        "(planted lactam/lactim InChIKey-collision duplicate) confirms the new structural-"
        "identity check applied here is capable of detecting the class of defect it targets. A "
        "genuine, previously-undisclosed corpus-construction defect was found in the course of "
        "this attack (2 duplicate structures hiding in the '350 canonically-distinct' corpus, "
        "root-caused to an atom-mapped-wildcard notation bug in the shared cap() convention) and "
        "is fully disclosed above; a materiality re-derivation on the truthful 348-structure "
        "corpus confirms it does not flip any of the 20 published verdicts, so it does not meet "
        "this item's specific refutation criterion and the survival verdict stands."
    ),
    "top_level_5_of_5_novel_headline_stands": True,
    "checks": diag["checks"],
    "checks_all_pass": diag["checks_all_pass"],
    "r_a07v2_receipt_path": R_A07V2_DONE,
    "r_a07v2_receipt_sha256": diag["r_a07v2_sha256"],
    "w_nov1_receipt_path": W_NOV1_DONE,
    "w_nov1_receipt_sha256": diag["w_nov1_sha256"],
    "dedup_set_sha256": diag["corpus"]["dedup_set_sha256"],
    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, qualification, regulatory or "
        "FTO authority. AUDIT_ONLY, ceiling EVIDENCE_ONLY.",
        "Does not create a new supersession: R-A07v2 remains the operative superseding artifact "
        "for R-A07; this receipt only independently re-verifies it (a second time) and closes "
        "campaign item V-A07v2.",
        "Does NOT repair the corpus_exchangeability_defect_found above -- that remains open for "
        "a future repair item; this receipt only discloses and materiality-checks it.",
        "The directive (AMPHORA-DIRECTIVE-2026-08-05) is AUDIT-ONLY: grants no promotion, "
        "procurement, safety, synthesis or freedom-to-operate authority.",
    ],
    "theory_reference": diag["theory_reference"],
    "rdkit_version": diag["rdkit_version"],
    "reproducibility": {
        "byte_identical": canon == runB,
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "harness_sha256": {"run_va07v2_verify.py": harness_sha},
        "replay_method": (
            "run_va07v2_verify.py executed twice with distinct output filenames "
            "(diagnostic.canonical.json, diagnostic.runB.json); payload serialized with "
            "json.dumps(sort_keys=True) each run and asserted byte-equal before signing."
        ),
        "two_replay_sha256_gate": "PASS",
    },
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "used_for": "AUDIT_ONLY done receipt under evidence/phase0/repairs/V-A07v2/done/",
        "derives_pinned_trust_store_key_id": True,
        "signs_phase0_evaluation_or_review": False,
    },
}
body = json.dumps(body_obj, sort_keys=True).encode()
payload_b64 = base64.b64encode(body).decode()
payload_type = "application/vnd.amphora.molecule-novelty-v-a07v2-done+json"
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
out_path = DONE / "v-a07v2-done-receipt.v1.dsse.json"
out_path.write_text(json.dumps(envelope, indent=2))
print("WROTE", out_path)
print("verdict:", body_obj["verdict"])
print("self_verify_ok: True")
print("sha256:", sha(out_path.read_bytes()))
