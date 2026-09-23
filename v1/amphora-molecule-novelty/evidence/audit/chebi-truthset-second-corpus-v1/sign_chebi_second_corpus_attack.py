#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-novelty ChEBI-truthset second-corpus
AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt under evidence/audit/;
does NOT sign a phase0 evaluation/review, does NOT promote authority, does NOT
flip scientific_readiness, does NOT modify the manifest, any locked dataset, or
the signed Phase-0 novelty KPI (supersede-never-rewrite: the KPI is a read-only
input to this audit, cited by sha256, never edited). Derived key_id
cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-novelty/evidence/audit/chebi-truthset-second-corpus-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260817T200001-2957460-5a8cbe99d90c"


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
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_chebi_second_corpus_attack.py").read_bytes())

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

body_obj = {
    "schema": "amphora.molecule-novelty.chebi-truthset-second-corpus-audit.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "NOVELTY_CHEBI_SMALL_MOLECULE_SECOND_CORPUS_ATTACK",
    "module": "amphora-molecule-novelty",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "attack_id": diag["attack_id"],
    "claim_under_attack": diag["claim_under_attack"],
    "refutation_criterion": diag["refutation_criterion"],
    "chebi_corpus": diag["chebi_corpus"],
    "openpoly_corpus_recap": diag["openpoly_corpus_recap"],
    "candidate_chebi_retest": diag["candidate_chebi_retest"],
    "anchor_check_openpoly_nn_matches_signed_kpi_exactly": diag["anchor_check_openpoly_nn_matches_signed_kpi_exactly"],
    "n_candidates_flipped_novel_to_not_novel_under_chebi_union": diag["n_candidates_flipped_novel_to_not_novel_under_chebi_union"],
    "n_candidates_with_exact_inchikey_skeleton_match_in_chebi": diag["n_candidates_with_exact_inchikey_skeleton_match_in_chebi"],
    "all_5_survive_chebi_union_corpus_novelty_below_0_40": diag["all_5_survive_chebi_union_corpus_novelty_below_0_40"],
    "featurization": diag["featurization"],
    "kpi_sha256": kpi_sha,
    "finding": (
        "The signed KPI's headline 'REAL FINDING: 5/5 candidates classified NOVEL' (NN "
        "Tanimoto < 0.40 vs the 350-distinct OpenPoly polymer corpus) does not survive "
        "re-testing against a categorically different, rights-clean, already in-tree "
        "reference corpus: ChEBI release-252 3-star curated small-molecule entities "
        "(50,383 canonically-distinct structures after dedup). 4 of 5 candidates flip "
        "from NOVEL to NOT-NOVEL under the union of OpenPoly-350 and ChEBI-dedup: DDS "
        "(NN Tanimoto 0.3929 -> 1.0, exact InChIKey-skeleton match to CHEBI:4325, "
        "4,4'-sulfonyldianiline), DETA (0.1667 -> 1.0, exact match to CHEBI:30629, "
        "diethylenetriamine), TETA (0.1579 -> 1.0, exact match to CHEBI:39501, "
        "triethylenetetramine), and m-XDA (0.2381 -> 0.7059 vs CHEBI:40538 "
        "benzylamine, no exact skeleton match but far above the 0.40 cut). Only IPDA "
        "(0.1667 -> 0.3548) remains below 0.40 against ChEBI and survives. Three "
        "candidates (DDS, DETA, TETA) are not merely 'similar to' but ARE already-"
        "cataloged ChEBI chemical entities by InChIKey-skeleton identity, independent "
        "of any Tanimoto threshold argument -- this is the strongest possible form of "
        "'not novel' available to a structural-similarity audit."
    ),
    "why_this_corpus_is_a_categorically_harder_test_than_the_prior_second_corpus": (
        "The 2026-08-13 W-D-NOV second-corpus attack (PolyInfo, another polymer "
        "repeat-unit corpus) SURVIVED because it, like OpenPoly, only contains capped "
        "polymer repeat-unit fragments -- structurally incapable of representing a "
        "discrete small-molecule commodity chemical as itself. ChEBI is a curated "
        "database of real, discrete small-molecule chemical entities, the correct-"
        "shaped corpus to catch 'this candidate is already a cataloged known compound.' "
        "It was already rights-cleared (DERIVATIVE_ALLOWED, CC-BY-4.0) and in-tree for "
        "amphora-molecule-property before this fire; this fire is the first to point it "
        "at amphora-molecule-novelty's candidates."
    ),
    "verdict": "CLAIM_REFUTED",
    "verdict_note": (
        "The KPI's 5/5-NOVEL headline, and by extension the 'novelty claims rest on "
        "more than one reference corpus' SURVIVED verdict from W-D-NOV "
        "(2026-08-13), do not generalize to a small-molecule reference corpus: 4/5 "
        "candidates are not novel by NN-Tanimoto once ChEBI is included, and 3/5 are "
        "literal cataloged-entity matches by InChIKey. This does not contest the raw "
        "OpenPoly-only NN-Tanimoto values themselves (anchor check passes exactly), "
        "only the headline's implicit generalization beyond the single OpenPoly corpus "
        "-- see finding and does_not_close."
    ),
    "scope_note": (
        "The KPI's own claim_locks already disclaim "
        "'reference_corpus_is_openpoly_only_not_a_comprehensive_prior_art_search' and "
        "'novelty_is_scaffold_and_fingerprint_similarity_only_not_novelty_in_uspto_sense' "
        "-- so this finding does not contradict the KPI's narrowly-scoped written text. "
        "It refutes the informally-relied-upon headline ('5/5 NOVEL') exactly the way "
        "W-D-NOV's own refutation_criterion was designed to test, using a corpus that "
        "actually is shaped to catch this failure mode where PolyInfo was not."
    ),
    "closes": [
        "Whether the 5/5-NOVEL headline is robust to the presence of a real small-"
        "molecule chemical-entity reference corpus in the union: NO -- 4/5 flip, 3/5 "
        "by exact cataloged-entity identity.",
    ],
    "does_not_close": [
        "Does not contest the raw OpenPoly-350-only NN-Tanimoto values (anchor check "
        "passes to 0 absolute error for all 5 candidates).",
        "Does not modify the KPI, its claim_locks, or any prior receipt "
        "(supersede-never-rewrite; this is a new open finding, not a supersession).",
        "Grants no batch-release, manufacturing-qualification, optimizer, product-"
        "performance, regulatory, safety, solver, or patentability/FTO authority -- "
        "and being 'already cataloged in ChEBI' is not itself a patentability/FTO "
        "determination either (ChEBI is a chemical-entity ontology, not a prior-art or "
        "USPTO/EPO search).",
        "Does not repair the KPI (no corrected headline or re-scoped claim_lock is "
        "proposed here); that is follow-up work for an R- campaign item, and should "
        "likely be coordinated with the two other still-open, unrepaired findings "
        "against this same KPI (citation-provenance-threshold-source-v1, "
        "conformal-novelty-significance-reattack-v1).",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "note": (
            "Fully deterministic pipeline (SHA-256-pinned OpenPoly CSV + SHA-256-pinned "
            "ChEBI SDF.gz, no RNG); two independent process invocations produced "
            "byte-identical diagnostic JSON (wall-clock timing excluded from the hashed "
            "payload)."
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
ptype = "application/vnd.amphora.molecule-novelty-chebi-truthset-second-corpus-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "chebi-truthset-second-corpus-receipt.v1.dsse.json"
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
