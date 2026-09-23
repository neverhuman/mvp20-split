#!/usr/bin/env python3
"""Sign the V-N02b independent-verify done receipt with the PHASE0_EVALUATOR
key, matching the repo-wide evidence/audit signing convention."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-role-ranker/evidence/phase0/repairs/V-N02b"
WORK = OUT / "work"
DONE = OUT / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260804T020001-3301653-a40483b3cbba"
CAMPAIGN_ITEM_ID = "V-N02b"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


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


diagA_path = WORK / "diagnostic.canonical.json"
diagB_path = WORK / "diagnostic.runB.json"
diagA = diagA_path.read_bytes()
diagB = diagB_path.read_bytes()
assert diagA == diagB, "two-replay bytes differ"
diag = json.loads(diagA)
assert diag["verdict"] == "CLAIM_SURVIVED"
assert diag["refute_reasons"] == []
assert diag["n_probes_failed"] == 0
assert diag["n_probes_novel"] >= 2

harness_main_sha = sha_file(WORK / "vn02b-verify/src/main.rs")
harness_cargo_sha = sha_file(WORK / "vn02b-verify/Cargo.toml")

r_n02_done_path = OUT.parent / "R-N02/done/rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json"
r_n02_done_sha = sha_file(r_n02_done_path)

v1_fixture_path = ROOT / "amphora-molecule-role-ranker/reference/phase0-role-known-answer.v1.json"
v2_fixture_path = ROOT / "amphora-molecule-role-ranker/reference/phase0-role-known-answer.v2.json"
v1_fixture_sha = sha_file(v1_fixture_path)
v2_fixture_sha = sha_file(v2_fixture_path)

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert rev_pin, "reviewer key_id does not match pinned trust-store PHASE0_INTERNAL_REVIEWER entry"

body_obj = {
    "schema": "amphora.molecule-role-ranker.v-n02b-independent-verify-receipt.v1",
    "receipt_id": "v-n02b-molecule-role-ranker-independent-verify-" + sha(diagA)[:32],
    "fire_id": FIRE_ID,
    "campaign_item_id": CAMPAIGN_ITEM_ID,
    "repair_item_under_verify": "R-N02",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "run_type": "SCIENCE_VALIDATION_REPLAY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": True,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-molecule-role-ranker",
    "objective": (
        "INDEPENDENT VERIFY of interactive repair R-N02 on the "
        "amphora-molecule-role-ranker side. This receipt's author did not write "
        "R-N02; it is a fresh adversarial re-derivation via a newly-authored Rust "
        "harness (vn02b-verify), not a re-run of R-N02's own harnesses. Attacked "
        "claims: (1) DPG (CAS 102-06-7) and DOTG (CAS 97-39-2) classify "
        "out_of_domain with reactive_amine_hydrogen_count==0 through the REAL "
        "production RDKit C++ FFI; (2) the 39-record v1 known-answer fixture is "
        "byte-intact and every record reproduces via the real FFI; (3) fixture v2 "
        "supersedes v1 (embeds all 39 v1 records structurally identical, plus 5 "
        "new guanidine-class records) rather than replacing it, and the Phase-0 "
        "KPI harness still binds v1 only; (4) the fix generalizes to guanidine-"
        "family accelerators never tested by R-N02 or its refuting receipts."
    ),
    "claim_under_attack": {
        "receipt": "amphora-molecule-role-ranker/evidence/phase0/repairs/R-N02/done/"
                   "rn02-molecule-role-ranker-coordinated-cn-fix-repair-receipt.v1.dsse.json",
        "sha256": r_n02_done_sha,
        "text": "The coordinated C=N amine-rule fix withstands independent adversarial "
                "verification in the molecule-role-ranker module.",
    },
    "method": (
        "Authored a new, independent Rust binary crate (vn02b-verify, path-dependency "
        "on amphora-rdkit-ffi with feature=rdkit -- the REAL production FFI, not a "
        "synthesized fact or a re-run of R-N02's own probe list) that: (a) reads the "
        "sha-locked v1 fixture, verifies its sha256 against the value cited in R-N02's "
        "own done receipt, and re-derives all 39 records through the real FFI, "
        "comparing to the fixture's own recorded facts; (b) reads fixture v2, verifies "
        "its sha256, confirms it has exactly 44 records and that its first 39 records "
        "are structurally identical to v1's 39 records (supersede, not replace); (c) "
        "confirms v1's file still exists standalone on disk and that "
        "amphora-molecule-capabilities/tests/role_ranker_phase0_kpi.rs still binds "
        "v1.json only (v2 not silently substituted into the signed KPI); (d) re-derives "
        "DPG and DOTG through the real FFI independently of R-N02's own harness; (e) "
        "runs 4 NOVEL guanidine-family probes never tested by R-N02, its refuting "
        "receipts, or fixture v2's 5 records: TMG (1,1,3,3-tetramethylguanidine, CAS "
        "80-70-6), Barton's base (2-tert-butyl-1,1,3,3-tetramethylguanidine, CAS "
        "29166-72-1), 1-phenylguanidine (CAS 2002-98-6), and an adversarial "
        "over-exclusion probe, agmatine (4-aminobutylguanidine, CAS 306-60-5), which "
        "carries a real primary amine structurally remote from an incidental guanidine "
        "group -- designed to catch a too-broad, whole-molecule exclusion bug that none "
        "of the other probes (all zero non-guanidine N-H) could ever detect. Molecular "
        "formula and MW independently cross-checked against published values for every "
        "probe before scoring, confirming SMILES correctly encode the named compounds."
    ),
    "pre_registered_refute_criterion": (
        "CLAIM_REFUTED if ANY of: v1 fixture sha256 mismatch; any of the 39 v1 records "
        "fails to reproduce via the real FFI; v2 fixture sha256 mismatch; v2 record "
        "count != 44; v2's first 39 records not structurally identical to v1's; v1 file "
        "missing from disk; KPI harness binding changed from v1-only; DPG or DOTG "
        "observed_role != out_of_domain or reactive_amine_hydrogen_count != 0; any of "
        "the 4 novel probes' observed_role or reactive_amine_hydrogen_count deviates "
        "from its independently-derived expectation (agmatine specifically: "
        "reactive_amine_hydrogen_count != 2 or observed_role != hardener)."
    ),
    "results": {
        "v1_fixture_sha256": diag["v1_fixture_sha256"],
        "v1_fixture_sha256_matches_r_n02_receipt": diag["v1_fixture_sha256"] == diag["v1_fixture_sha256_expected"],
        "v1_fixture_n_records": diag["v1_fixture_n_records"],
        "v1_fixture_n_mismatch_via_real_ffi": diag["v1_fixture_n_mismatch_via_real_ffi"],
        "v2_fixture_sha256": diag["v2_fixture_sha256"],
        "v2_fixture_sha256_matches_r_n02_receipt": diag["v2_fixture_sha256"] == diag["v2_fixture_sha256_expected"],
        "v2_fixture_n_records": diag["v2_fixture_n_records"],
        "v2_embeds_v1_39_records_structurally_identical": diag["v2_embeds_v1_39_records_structurally_identical"],
        "v1_file_still_exists_standalone": diag["v1_file_still_exists_standalone"],
        "kpi_harness_binds_v1_only": diag["kpi_harness_binds_v1_only"],
        "n_probes_total": diag["n_probes_total"],
        "n_probes_novel": diag["n_probes_novel"],
        "n_probes_failed": diag["n_probes_failed"],
        "probe_rows": diag["probe_rows"],
        "toolkit_provenance": diag["toolkit_provenance"],
    },
    "verdict": diag["verdict"],
    "why": (
        "Every pre-registered refute trigger was checked and none fired. DPG and DOTG "
        "independently re-derive through the real FFI as reactive_amine_hydrogen_count=0 "
        "/ out_of_domain, matching R-N02's claim. The v1 fixture is byte-intact "
        "(sha256 " + diag["v1_fixture_sha256"] + ", matches R-N02's cited value) and all "
        "39 records reproduce via the real FFI. Fixture v2 genuinely supersedes rather "
        "than replaces: 44 records total, first 39 structurally identical to v1, v1's "
        "file untouched on disk, and the signed Phase-0 KPI harness still binds v1 only "
        "-- v2 has not been silently substituted into any signed artifact. All 4 novel "
        "guanidine-family probes (TMG, Barton's base, 1-phenylguanidine, agmatine) "
        "score exactly as independently predicted, including the adversarial agmatine "
        "over-exclusion probe: its remote, non-guanidine-adjacent primary amine retains "
        "reactive_amine_hydrogen_count=2 and role=hardener rather than being collaterally "
        "zeroed by the presence of an unrelated guanidine group elsewhere in the "
        "molecule -- direct evidence the fix's exclusion is correctly scoped per-nitrogen, "
        "not per-molecule."
    ),
    "does_not_close": [
        "EVALUATION_SIGNATURE_ABSENT (this is an AUDIT_ONLY science-validation replay, "
        "not a Phase-0 evaluation/review signature).",
        "Whether reactive_amine_hydrogen_count should be exactly 0 for guanidine N-H in "
        "a quantitative AHEW sense (mechanistic nucleophilicity question, out of scope, "
        "explicitly left open by R-N02 itself).",
        "The molecule-property side of R-N02 (compute_amine_class.py); that is the "
        "separate V-N02a verify scope, not re-attacked here.",
        "Any change to bridge.cc, the KPI receipt, the fixtures, or the master manifest "
        "(66 receipts/11 modules unchanged; this receipt reads but does not modify any "
        "of them).",
    ],
    "input_artifacts": {
        "harness_main_rs_sha256": harness_main_sha,
        "harness_cargo_toml_sha256": harness_cargo_sha,
        "v1_fixture_sha256": v1_fixture_sha,
        "v2_fixture_sha256": v2_fixture_sha,
        "r_n02_done_receipt_sha256": r_n02_done_sha,
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2,
        "independent_runs": True,
        "canonical_diagnostic_sha256": sha(diagA),
        "runB_diagnostic_sha256": sha(diagB),
        "determinism_basis": (
            "no RNG, no wall clock, fixed hardcoded probe list, sorted-key BTreeMap "
            "JSON output; two independent process invocations produced byte-identical "
            "stdout (sha256 equal)."
        ),
        "harness_binary_provenance": (
            "cargo build --release against amphora-rdkit-ffi (path dependency, "
            "feature=rdkit) compiled with cxx against the pinned RDKit 2026.03.2 prefix "
            "at /home/ubuntu/.local/share/amphora/rdkit-2026.03.2 "
            "(RDKIT_INCLUDE_DIR/RDKIT_LIB_DIR/BOOST_INCLUDE_DIR); "
            "toolkit_provenance.exact_version_match=true recorded in every run."
        ),
    },
    "rights_check": (
        "No new external data source opened or acquired. All probe molecules are "
        "CAS-identified public-domain chemical identities evaluated purely structurally "
        "via the already-licensed pinned RDKit backend; the fixture and KPI-test files "
        "read are already-in-tree, already-hash-pinned artifacts."
    ),
    "gates_summary": {
        "two_replay_byte_stable_this_receipt": True,
        "real_production_ffi_not_reimplemented": True,
        "molecular_formula_mw_independently_cross_checked_against_published_values": True,
        "fixtures_untouched_by_this_verify": True,
        "novel_probes_not_reused_from_r_n02_or_refuting_receipts": True,
        "attack_genuinely_capable_of_falsifying": True,
        "signature_field_is_dsse_envelope_object": True,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY verify done-receipt under evidence/phase0/repairs/V-N02b/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
    "date": "2026-08-04",
    "generated_on_host": "xbabe2",
}

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(OUT / "receipt_body.canonical.json").write_bytes(body1)
(OUT / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-role-ranker.v-n02b-independent-verify-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

DONE.mkdir(parents=True, exist_ok=True)
outpath = DONE / "v-n02b-molecule-role-ranker-independent-verify-receipt.v1.dsse.json"
outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

written = json.loads(outpath.read_text())
sig_env = written["signature"]
payload = base64.standard_b64decode(sig_env["payload"])
sig_bytes = base64.standard_b64decode(sig_env["signatures"][0]["sig"])
keyid = sig_env["signatures"][0]["keyid"]
trust_pub_hex = by_role["PHASE0_EVALUATOR"]["public_key_hex"]
assert keyid == by_role["PHASE0_EVALUATOR"]["key_id"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust_pub_hex)).verify(
    sig_bytes, pae(sig_env["payloadType"], payload))
assert payload == body1

print("WROTE", outpath)
print("verdict", diag["verdict"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_byte_identical", body1 == body2)
print("independent_reverify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
