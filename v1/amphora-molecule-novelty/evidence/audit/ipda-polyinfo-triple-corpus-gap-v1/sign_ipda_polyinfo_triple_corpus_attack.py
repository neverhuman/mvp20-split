#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-novelty IPDA PolyInfo/triple-corpus gap
audit. AUDIT_ONLY: signs an audit receipt under evidence/audit/; does NOT sign a
phase0 evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the manifest, any locked dataset, the signed
Phase-0 novelty KPI, W-D-NOV, or chebi-truthset-second-corpus-v1 (supersede-never-
rewrite: all are read-only inputs cited by sha256, never edited). Derived key_id
cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-novelty/evidence/audit/ipda-polyinfo-triple-corpus-gap-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260819T140001-505064-6fba7d1dc072"


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


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
mutate = (BENCH / "diagnostic.mutate.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
mutate_diag = json.loads(mutate)
harness_sha = sha((BENCH / "run_ipda_polyinfo_triple_corpus_attack.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key does not match pinned Phase-0 trust store"

kpi_path = ROOT / "amphora-molecule-novelty/evidence/phase0/kpis/tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json"
kpi_sha = sha(kpi_path.read_bytes())
chebi_truthset_receipt_path = ROOT / "amphora-molecule-novelty/evidence/audit/chebi-truthset-second-corpus-v1/chebi-truthset-second-corpus-receipt.v1.dsse.json"
chebi_truthset_receipt_sha = sha(chebi_truthset_receipt_path.read_bytes())
ipda_chebi_propagation_receipt_path = ROOT / "amphora-molecule-novelty/evidence/audit/ipda-structural-correction-propagation-chebi-v1/ipda-structural-correction-propagation-chebi-receipt.v1.dsse.json"
ipda_chebi_propagation_receipt_sha = sha(ipda_chebi_propagation_receipt_path.read_bytes())
w_d_nov_receipt_path = ROOT / "amphora-molecule-novelty/evidence/phase0/repairs/W-D-NOV/done/W-D-NOV-second-corpus-novelty-retest-receipt.v1.dsse.json"
w_d_nov_receipt_sha = sha(w_d_nov_receipt_path.read_bytes())
ra07v2_path = ROOT / "amphora-molecule-novelty/evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json"
ra07v2_sha = sha(ra07v2_path.read_bytes())

body_obj = {
    "schema": "amphora.molecule-novelty.ipda-polyinfo-triple-corpus-gap-audit.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "IPDA_POLYINFO_TRIPLE_CORPUS_GAP_AUDIT",
    "module": "amphora-molecule-novelty",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_chebi_truthset_second_corpus_v1_receipt": False,
    "modifies_w_d_nov_receipt": False,
    "attack_id": diag["attack_id"],
    "claim_under_attack": diag["claim_under_attack"],
    "gap_alleged": diag["gap_alleged"],
    "refutation_criterion": diag["refutation_criterion"],
    "openpoly_corpus_recap": diag["openpoly_corpus_recap"],
    "chebi_corpus_recap": diag["chebi_corpus_recap"],
    "polyinfo_corpus_recap": diag["polyinfo_corpus_recap"],
    "triple_union_corpus_size": diag["triple_union_corpus_size"],
    "ipda_result": diag["ipda_result"],
    "material_flip_or_match_found": diag["material_flip_or_match_found"],
    "anchor_check_openpoly_nn_matches_signed_r_a07v2_value": diag["anchor_check_openpoly_nn_matches_signed_r_a07v2_value"],
    "anchor_check_chebi_nn_matches_2026_08_18_corrected_value": diag["anchor_check_chebi_nn_matches_2026_08_18_corrected_value"],
    "featurization": diag["featurization"],
    "kpi_sha256": kpi_sha,
    "chebi_truthset_second_corpus_v1_receipt_sha256": chebi_truthset_receipt_sha,
    "ipda_structural_correction_propagation_chebi_v1_receipt_sha256": ipda_chebi_propagation_receipt_sha,
    "w_d_nov_second_corpus_receipt_sha256": w_d_nov_receipt_sha,
    "r_a07v2_repair_receipt_sha256": ra07v2_sha,
    "finding": (
        "Two gaps closed in a single fire. (1) W-D-NOV's second-corpus attack "
        "(2026-08-13) hard-coded IPDA as the C9H20N2 demethylated structure already "
        "refuted by candidate-structure-identity-audit-v1 (2026-08-03) -- the same "
        "undisclosed-non-propagation defect ipda-structural-correction-propagation-"
        "chebi-v1 (2026-08-18) found in the ChEBI-corpus fire also afflicted the "
        "PolyInfo-corpus fire, so IPDA vs PolyInfo-dedup under its correct R-A07v2 "
        "v2_canonical structure had never been computed. (2) no fire had ever tested "
        "any candidate against the TRIPLE union of all three rights-clean corpora "
        "this module now has pinned in-tree (OpenPoly-350 + ChEBI-dedup-50383 + "
        "PolyInfo-dedup-12370) -- each second corpus was only ever unioned with "
        "OpenPoly alone, never with each other."
    ),
    "recomputation_result": (
        "Under the correct R-A07v2 v2_canonical IPDA structure ('CC1(C)CC(N)CC(C)"
        "(CN)C1', C10H22N2), NN Tanimoto vs PolyInfo-dedup (12,370 structures) is "
        f"{diag['ipda_result']['nn_tanimoto_vs_polyinfo_dedup']} (wrong-structure "
        "W-D-NOV fire reported 0.28125 for this corpus; both values are well below "
        "0.40 and this fire's corrected figure is the first ever computed on the "
        "right molecule). No InChIKey-skeleton match to any PolyInfo entity. NN "
        f"Tanimoto vs the triple-union corpus (63,103 distinct structures) is "
        f"{diag['ipda_result']['nn_tanimoto_vs_triple_union_corpus']}, driven by the "
        "ChEBI nearest neighbour (the same isophorone-diisocyanate-shaped CHEBI:53214 "
        "hit R-A07v2/ipda-structural-correction-propagation-chebi-v1 already "
        "reported) -- adding PolyInfo to the reference universe does not move the "
        "union nearest neighbour, since PolyInfo's own best IPDA match "
        f"({diag['ipda_result']['nn_tanimoto_vs_polyinfo_dedup']}) is farther than "
        "the ChEBI one. IPDA remains classified NOVEL against every individual "
        "corpus and the full triple union. OpenPoly and ChEBI anchor values "
        "reproduce their previously-signed figures to 0 absolute error."
    ),
    "verdict": "CLAIM_SURVIVED",
    "verdict_note": (
        "IPDA's novelty claim survives the broadest and most heavily-relied-upon "
        "corpus-coverage test this module has ever assembled against it: the joint "
        "triple union of every rights-clean reference structure library currently "
        "pinned in-tree (63,103 distinct structures total), computed for the first "
        "time ever under IPDA's correct structure against PolyInfo specifically. "
        "This does not resolve or touch the other three still-open, unrepaired "
        "findings against the KPI's flat '5/5 NOVEL' headline (citation-provenance-"
        "threshold-source-v1, conformal-novelty-significance-reattack-v1, "
        "chebi-truthset-second-corpus-v1 for DDS/DETA/TETA/m-XDA) -- IPDA specifically "
        "is, and remains, the sole candidate never shown to collide with any "
        "reference corpus this module has assembled."
    ),
    "scope_note": (
        "Does not contest DDS/DETA/TETA/m-XDA (not recomputed here; their PolyInfo "
        "and ChEBI comparisons were never affected by the IPDA structural-correction "
        "defect, since none of them ever had a structural correction issued). Does "
        "not modify the KPI, W-D-NOV, chebi-truthset-second-corpus-v1, or "
        "ipda-structural-correction-propagation-chebi-v1 (supersede-never-rewrite; "
        "this closes a coverage gap, it does not correct a reported figure, so no "
        "RETRACTION-INDEX entry is added)."
    ),
    "does_not_close": [
        "Does not repair the three still-open findings against the KPI's flat "
        "'5/5 NOVEL' headline (citation-provenance-threshold-source-v1, "
        "conformal-novelty-significance-reattack-v1, chebi-truthset-second-corpus-v1).",
        "Does not re-test DDS/DETA/TETA/m-XDA against PolyInfo under any structural "
        "correction (none is needed for them) or against the triple union (left for "
        "a follow-up fire; those four are already known NOT-NOVEL against ChEBI "
        "alone, so a triple-union re-test cannot make them MORE novel).",
        "Grants no batch-release, manufacturing-qualification, optimizer, product-"
        "performance, regulatory, safety, solver, or patentability/FTO authority.",
    ],
    "positive_control": mutate_diag["positive_control"],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "mutate_diagnostic_sha256": sha(mutate),
        "harness_sha256": harness_sha,
        "note": (
            "Fully deterministic pipeline (SHA-256-pinned OpenPoly CSV + SHA-256-"
            "pinned ChEBI SDF.gz + SHA-256-pinned PolyInfo_p.csv, no RNG); two "
            "independent process invocations of the canonical (non-mutate) mode "
            "produced byte-identical diagnostic JSON (wall-clock timing excluded "
            "from the hashed payload)."
        ),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-novelty-ipda-polyinfo-triple-corpus-gap-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "ipda-polyinfo-triple-corpus-gap-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
