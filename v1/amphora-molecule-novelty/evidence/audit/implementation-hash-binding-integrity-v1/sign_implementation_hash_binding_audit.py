#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-molecule-novelty implementation-source-hash
-binding-integrity AUDIT_ONLY receipt. AUDIT_ONLY: signs an audit receipt
under evidence/audit/; does NOT sign a phase0 evaluation/review, does NOT
promote authority, does NOT flip scientific_readiness, does NOT modify the
manifest, any locked dataset, or the signed Phase-0 novelty KPI. Does NOT
edit docs/mission.md or docs/capability-profile.json (repair, if pursued,
is separate follow-up work under an R- campaign item). Derived key_id
cross-checked vs pinned trust store.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-molecule-novelty/evidence/audit/implementation-hash-binding-integrity-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


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
harness_sha = sha((BENCH / "run_implementation_hash_binding_audit.py").read_bytes())

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
assert diag["n_mismatched"] == 3 and diag["n_targets_checked"] == 3

body_obj = {
    "schema": "amphora.molecule-novelty.implementation-hash-binding-integrity-audit.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "NOVELTY_IMPLEMENTATION_SOURCE_HASH_BINDING_INTEGRITY_AUDIT",
    "module": "amphora-molecule-novelty",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_mission_or_capability_profile": False,
    "attack_type": diag["attack"],
    "claim_under_attack": (
        "docs/mission.md ('Honest current state') and docs/capability-profile.json "
        "(evidence_inventory.implementation.sha256, "
        "evidence_inventory.implementation.version_source_sha256, "
        "evidence_inventory.runtime_integration.registry_sha256) bind this module's "
        "live checked implementation, its Cargo.toml version source, and its "
        "amphora-engine adapter registration to three specific SHA-256 hashes, "
        "presented as the current, honest, checked state of the module's authority chain."
    ),
    "background": (
        "A same-day sibling fire (fire_id 20260816T130001-3022527-0af70e0219bf, module "
        "amphora-molecule-generator, ledgered verdict REFUTED) found the SAME "
        "amphora-molecule-capabilities/src/lib.rs implementation-hash citation stale in "
        "its own module's docs, and separately noted the identical stale hash also "
        "appears in 4 other modules' docs including amphora-molecule-novelty's, but "
        "explicitly scoped verifying/fixing that out of its own fire as 'context only, "
        "out of this module's scope to fix'. This audit is the in-scope follow-through "
        "for amphora-molecule-novelty: it (a) independently re-derives the mismatch from "
        "scratch rather than trusting the sibling fire's numbers, (b) extends coverage to "
        "two hash citations the sibling fire never checked at all "
        "(version_source_sha256 against Cargo.toml, registry_sha256 against "
        "amphora-engine/src/lib.rs), and (c) establishes WHEN each mismatch originated "
        "via git blob history, which the sibling fire did not attempt."
    ),
    "method": (
        "For each of the 3 claimed (path, sha256) bindings in "
        "docs/capability-profile.json: computed sha256 of the current working-tree file; "
        "computed sha256 of the git HEAD blob for that path via `git show HEAD:<path>` "
        "(raw bytes, not text-decoded, to avoid a newline-normalization corruption bug "
        "caught and fixed during this audit's own development -- see "
        "self_correcting_near_miss); ran `git status --porcelain -- <path>` to confirm no "
        "uncommitted local edits; ran `git log --oneline -- <path>` to count commits "
        "touching the file and identify the introducing commit. A citation is judged "
        "'wrong since inception' (not later drift) when: working tree matches HEAD blob "
        "(git_working_tree_clean_for_this_file=true, git_head_blob_matches_working_"
        "tree=true) AND the file has exactly 1 commit in its history -- i.e. the claimed "
        "hash never matched the file at any point git has recorded."
    ),
    "self_correcting_near_miss": (
        "First implementation of the git-HEAD-blob check used "
        "subprocess.run(text=True).stdout.strip() for `git show HEAD:<path>`, which "
        "silently stripped trailing-newline bytes from the retrieved blob before hashing, "
        "producing a DIFFERENT wrong hash (e.g. a5e4e672... for lib.rs) than either the "
        "claimed citation OR the true working-tree hash, and made every target look like "
        "'HEAD does not match working tree' (false positive for uncommitted drift). "
        "Root-caused to the .strip() call; fixed by reading `git show` output as raw "
        "bytes via subprocess with no text mode and no stripping. Cross-checked the fix "
        "against the raw shell command `git show HEAD:<path> | sha256sum` run "
        "independently outside the harness for all 3 targets -- byte-identical to the "
        "harness's post-fix actual_git_head_blob_sha256 in every case."
    ),
    "checks": diag["checks"],
    "n_targets_checked": diag["n_targets_checked"],
    "n_mismatched": diag["n_mismatched"],
    "mismatched_labels": diag["mismatched_labels"],
    "n_mismatched_wrong_since_inception": diag["n_mismatched_wrong_since_inception"],
    "mismatched_wrong_since_inception_labels": diag["mismatched_wrong_since_inception_labels"],
    "capability_profile_automatic_demotion_triggers": diag["capability_profile_automatic_demotion_triggers"],
    "source_hash_mutation_is_declared_automatic_demotion_trigger": diag["source_hash_mutation_is_declared_automatic_demotion_trigger"],
    "policy_self_contradiction": diag["policy_self_contradiction"],
    "finding": (
        "All 3 of 3 checked source-hash bindings in this module's own docs are wrong, "
        "and all 3 were wrong from the single commit (907e753, 'baseline: post-Wave-R+ "
        "evidence tree, 2026-08-03T23:30Z') that introduced them -- not later drift. "
        "(1) implementation: claimed 5968f518f199cf697d153018afdfee887e9b3ec0bee8a9c00d"
        "cc3c5a854ec861 for amphora-molecule-capabilities/src/lib.rs; actual "
        "258043a42c015587600da417a50170928b57f4f2eb2a0bfcee9b0ac14ada750c. "
        "(2) version_source: claimed d07286abf1e2853d73f996f57c784310c801e46872e68e9f8c7"
        "9ca95cba2e9c6 for amphora-molecule-capabilities/Cargo.toml; actual "
        "7458e4ed581f9296efdf7b27a39f707e1974c642fb3768c8ab18cfadc04a5416. "
        "(3) registry: claimed 6b007d7d9d0acd453aac5e7c300ab16fb9a7253337c722cc4cffe0be2"
        "3db62b4 for amphora-engine/src/lib.rs; actual "
        "ddfd50fcebf96b096fff8406dfe27b512ab8e88564f76b644ffda776df662abb. "
        "capability-profile.json's own automatic_demotion list names 'source hash "
        "mutation' as a trigger; since git history shows these were never correct (no "
        "commit exists where they matched), this is not even a demotion-triggering "
        "mutation but a citation that was fabricated or miscomputed at authorship time "
        "and has stood unverified in the module's authority-chain docs ever since."
    ),
    "verdict": "CLAIM_REFUTED",
    "verdict_note": (
        "The claim that docs/mission.md and docs/capability-profile.json honestly and "
        "currently bind amphora-molecule-novelty's implementation, version source, and "
        "runtime registry to the cited SHA-256 hashes is REFUTED: 3/3 checked citations "
        "are wrong, confirmed wrong since the single commit that introduced them (not "
        "drift), by independent git-blob re-derivation. This does not contest that the "
        "cited PATHS are the correct live implementation files -- amphora-engine/src/"
        "lib.rs registration and amphora-molecule-capabilities/src/lib.rs as the checked "
        "Rust implementation are corroborated elsewhere in this and sibling modules -- "
        "only that the specific hash values asserted for provenance-binding are wrong."
    ),
    "closes": [
        "Whether amphora-molecule-novelty's own implementation/version-source/registry "
        "hash citations are currently correct: NO, none of the 3 checked are.",
        "Whether this is unrecorded drift after a correct baseline vs. a citation that "
        "was never correct: confirmed the latter for all 3 (single-commit history, clean "
        "git status, working tree matches HEAD).",
    ],
    "does_not_close": [
        "Does not contest that the cited file PATHS are the correct live implementation, "
        "version source, and registry files for this module.",
        "Does not contest any Tanimoto-NN novelty score, conformal table, or KPI "
        "numeric result from prior audits -- this audit does not touch "
        "evidence/phase0/kpis/ or the scientific receipt.",
        "Does not repair the citations (no corrected hash is written into mission.md or "
        "capability-profile.json here); that is follow-up work for an R- campaign item, "
        "consistent with repair-mode discipline (supersede, never silently rewrite).",
        "Grants no batch-release, manufacturing-qualification, product-performance, "
        "regulatory, safety, solver, or patentability/FTO authority.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
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
ptype = "application/vnd.amphora.molecule-novelty-implementation-hash-binding-integrity-audit+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
out = BENCH / "implementation-hash-binding-integrity-receipt.v1.dsse.json"
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
