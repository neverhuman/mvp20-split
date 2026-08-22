#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-novelty IPDA structural-correction
propagation audit applied to chebi-truthset-second-corpus-v1. AUDIT_ONLY:
signs an audit receipt under evidence/audit/; does NOT sign a phase0
evaluation/review, does NOT promote authority, does NOT flip
scientific_readiness, does NOT modify the manifest, any locked dataset, the
signed Phase-0 novelty KPI, or the chebi-truthset-second-corpus-v1 receipt
(supersede-never-rewrite: both are read-only inputs cited by sha256, never
edited). Derived key_id cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-novelty/evidence/audit/ipda-structural-correction-propagation-chebi-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260818T080001-1050990-302eac36604a"


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
harness_sha = sha((BENCH / "run_ipda_correction_chebi_attack.py").read_bytes())

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
ra07v2_path = ROOT / "amphora-molecule-novelty/evidence/phase0/repairs/R-A07v2/done/r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json"
ra07v2_sha = sha(ra07v2_path.read_bytes())

body_obj = {
    "schema": "amphora.molecule-novelty.ipda-structural-correction-propagation-chebi-audit.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "IPDA_STRUCTURAL_CORRECTION_PROPAGATION_AUDIT_ON_CHEBI_SECOND_CORPUS_FINDING",
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
    "attack_id": diag["attack_id"],
    "claim_under_attack": diag["claim_under_attack"],
    "defect_alleged": diag["defect_alleged"],
    "refutation_criterion": diag["refutation_criterion"],
    "chebi_corpus_recap": diag["chebi_corpus_recap"],
    "openpoly_corpus_recap": diag["openpoly_corpus_recap"],
    "ipda_as_reported_by_chebi_truthset_v1_wrong_structure": diag["ipda_as_reported_by_chebi_truthset_v1_wrong_structure"],
    "ipda_recomputed_correct_structure": diag["ipda_recomputed_correct_structure"],
    "delta_nn_tanimoto_vs_chebi_wrong_minus_correct": diag["delta_nn_tanimoto_vs_chebi_wrong_minus_correct"],
    "material_flip_between_wrong_and_correct_structure": diag["material_flip_between_wrong_and_correct_structure"],
    "anchor_check_openpoly_nn_matches_signed_r_a07v2_value": diag["anchor_check_openpoly_nn_matches_signed_r_a07v2_value"],
    "featurization": diag["featurization"],
    "kpi_sha256": kpi_sha,
    "chebi_truthset_second_corpus_v1_receipt_sha256": chebi_truthset_receipt_sha,
    "r_a07v2_repair_receipt_sha256": ra07v2_sha,
    "finding": (
        "chebi-truthset-second-corpus-v1 (2026-08-17, still-open, unrepaired) reported "
        "IPDA as 'the sole survivor' of novelty across every reference corpus tested "
        "(NN Tanimoto vs ChEBI-dedup 0.354838...). Its own CANDS['IPDA'] hard-codes "
        "'CC1(CC(CC(C1)N)C)CN' -- byte-identical to the C9H20N2 demethylated string "
        "R-A07v2's corrected_ipda block records as 'superseded_smiles' / "
        "'superseded_formula': 'C9H20N2', and which candidate-structure-identity-"
        "audit-v1 (2026-08-03) independently showed is NOT real isophorone diamine "
        "(CAS 2855-13-2, C10H22N2 -- missing a ring methyl). Five prior fires "
        "(R-A07, V-A07, R-A07v2, W-NOV1, V-A07v2) established the R-A07v2 "
        "'v2_canonical' structure 'CC1(C)CC(N)CC(C)(CN)C1' (C10H22N2) as authoritative "
        "going forward. chebi-truthset-second-corpus-v1's 2026-08-17 script "
        "nonetheless copied IPDA's SMILES straight from the signed KPI's own "
        "candidate_smiles field (which, correctly, is never edited under "
        "supersede-never-rewrite) rather than from the retraction-index-recorded "
        "correction -- the same undisclosed-non-propagation failure mode V-A07 found "
        "in R-A07 fourteen days earlier, recurring in a brand-new analysis."
    ),
    "recomputation_result": (
        "Recomputed IPDA's NN Tanimoto against the identical SHA-256-pinned ChEBI-"
        "dedup corpus using the correct R-A07v2 v2_canonical structure: 0.333333 "
        "(vs the wrong structure's reported 0.354838, delta -0.021505). Both values "
        "stay well below the 0.40 cut; no InChIKey-skeleton match appears or "
        "disappears (neither structure matches any ChEBI entity by skeleton "
        "identity); novel_vs_chebi_dedup=True under both structures -- "
        "material_flip=False. The OpenPoly-only anchor value (0.16666666666666666) "
        "is confirmed numerically unchanged between the two structures, matching "
        "R-A07v2's own prior finding for that corpus."
    ),
    "verdict": "CLAIM_REFUTED",
    "verdict_note": (
        "REFUTED, scoped exactly the way V-A07 was scoped against R-A07: the SPECIFIC "
        "reported figure (chebi-truthset-second-corpus-v1's IPDA-vs-ChEBI NN Tanimoto "
        "0.354838 and its underlying candidate_smiles) is computed on a structure this "
        "module's own retraction index had already established as refuted two weeks "
        "earlier, and is therefore false as a description of isophorone diamine's real "
        "similarity to the ChEBI corpus -- the true value is 0.333333. The qualitative "
        "headline this specific number was used to support ('IPDA alone survives, NOVEL "
        "vs ChEBI') is NOT overturned by the correction -- if anything the correct "
        "structure is chemically FARTHER from any ChEBI entry, not closer -- so this is "
        "a provenance/propagation defect, not a new novelty flip. This does not "
        "reverse chebi-truthset-second-corpus-v1's own overall CLAIM_REFUTED verdict "
        "against the KPI's 5/5-NOVEL headline (DDS/DETA/TETA/m-XDA results are "
        "untouched, their SMILES never had a structural correction issued against "
        "them) -- it corrects one specific number inside that still-open finding."
    ),
    "scope_note": (
        "Does not contest DDS/DETA/TETA/m-XDA's reported ChEBI comparisons (not "
        "recomputed here; none of those candidates has ever had a structural "
        "correction issued, so no propagation defect is possible for them). Does not "
        "modify the KPI, R-A07v2, or chebi-truthset-second-corpus-v1 (supersede-never-"
        "rewrite; this is a new open finding layered on an existing open finding, not "
        "a supersession -- chebi-truthset-second-corpus-v1 itself remains an accurate "
        "record of what its own script computed, now with a disclosed input defect)."
    ),
    "closes": [
        "Whether chebi-truthset-second-corpus-v1's specific IPDA-vs-ChEBI NN Tanimoto "
        "figure (0.354838) is computed on the correct, retraction-index-established "
        "candidate structure: NO -- it uses the superseded C9H20N2 structure. The "
        "correct figure is 0.333333.",
        "Whether using the correct structure changes IPDA's novel/not-novel "
        "classification vs ChEBI, or produces a new InChIKey-skeleton match: NO -- "
        "still NOVEL (< 0.40), still no exact-entity match, in fact a slightly wider "
        "margin.",
    ],
    "does_not_close": [
        "Does not repair chebi-truthset-second-corpus-v1's IPDA figure in place "
        "(supersede-never-rewrite) -- a follow-up R- campaign item should either "
        "append a superseding entry to this module's RETRACTION-INDEX.md for the "
        "IPDA-vs-ChEBI figure specifically, or fold this correction into whatever "
        "R- item eventually retires the flat '5/5 NOVEL' headline (already flagged "
        "as needed by chebi-truthset-second-corpus-v1's own 'not yet repaired' note).",
        "Does not touch the two other still-open, unrepaired findings against the "
        "same KPI (citation-provenance-threshold-source-v1, "
        "conformal-novelty-significance-reattack-v1).",
        "Grants no batch-release, manufacturing-qualification, optimizer, product-"
        "performance, regulatory, safety, solver, or patentability/FTO authority.",
    ],
    "positive_control_self_check": {
        "description": (
            "Companion run with --mutate re-injects the SAME wrong structure into "
            "both the 'as-reported' and 'recomputed' slots, forcing structures_differ="
            "False, to prove this audit's own wrong-vs-correct diff machinery reports "
            "a null result (delta=0.0, material_flip=False) when there is genuinely "
            "nothing to detect, rather than vacuously always firing a difference."
        ),
        "mutate_run_result": {
            "structures_differ": mutate_diag["ipda_as_reported_by_chebi_truthset_v1_wrong_structure"]["candidate_smiles"] == mutate_diag["ipda_recomputed_correct_structure"]["candidate_smiles"],
            "delta_nn_tanimoto_vs_chebi": mutate_diag["delta_nn_tanimoto_vs_chebi_wrong_minus_correct"],
            "material_flip": mutate_diag["material_flip_between_wrong_and_correct_structure"],
        },
        "canonical_run_result": {
            "structures_differ": diag["ipda_as_reported_by_chebi_truthset_v1_wrong_structure"]["candidate_smiles"] != diag["ipda_recomputed_correct_structure"]["candidate_smiles"],
            "delta_nn_tanimoto_vs_chebi": diag["delta_nn_tanimoto_vs_chebi_wrong_minus_correct"],
        },
        "note": "This CLAIM_REFUTED verdict does not itself require a positive control (only CLAIM_SURVIVED does); this self-check is included anyway as evidence the diff pipeline discriminates rather than always reporting a difference.",
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "mutate_diagnostic_sha256": sha(mutate),
        "harness_sha256": harness_sha,
        "note": (
            "Fully deterministic pipeline (SHA-256-pinned OpenPoly CSV + SHA-256-pinned "
            "ChEBI SDF.gz, no RNG); two independent process invocations of the canonical "
            "(non-mutate) mode produced byte-identical diagnostic JSON (wall-clock timing "
            "excluded from the hashed payload)."
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
ptype = "application/vnd.amphora.molecule-novelty-ipda-structural-correction-propagation-chebi-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "ipda-structural-correction-propagation-chebi-receipt.v1.dsse.json"
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
