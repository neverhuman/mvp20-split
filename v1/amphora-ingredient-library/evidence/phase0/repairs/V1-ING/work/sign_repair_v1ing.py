#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V1-ING repair done-receipt (amphora-ingredient-library).

Construction replicated from R-A01's sign_repair_ra01.py / the in-tree
sign_canon_invariance.py lineage: pae(), load_seed(), payloadType naming,
envelope fields, trust-store key pinning. Signs under
evidence/phase0/repairs/V1-ING/done/; does NOT promote authority, flip
scientific_readiness, or modify any existing receipt, the portfolio
manifest, any locked dataset, or the falsification ledger.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-ingredient-library"
CC_DIR = MOD / "evidence/audit/constant-crosscheck-v1"
REFUTING = MOD / "evidence/audit/eew-solid-band-mislabel-gap-v1/eew-solid-band-mislabel-gap-receipt.v1.dsse.json"
RA01_DONE = MOD / "evidence/phase0/repairs/R-A01/done/repair-R-A01-done-receipt.v1.dsse.json"
REPAIR = MOD / "evidence/phase0/repairs/V1-ING"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
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


# ---- live-code fix provenance ---------------------------------------------
script_path = CC_DIR / "run_crosscheck.py"
script_sha_after = sha(script_path.read_bytes())
SHA_BEFORE = "ea99c0a2eefbc5e3cc36c64ada54c131d2e38833f6821a65ad3f09f68e81aedb"
assert script_sha_after == "bfcc550a226e31c73ac3ab89253447f254b468a64eae223470872e5e30917bc2", script_sha_after

# ---- live re-run (two independent OS-process replays) ---------------------
runA = (WORK / "diagnostic.runA.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert runA == runB, "two-replay bytes differ"
diag_sha = sha(runA)
diag = json.loads(runA)
assert diag["schema"] == "amphora.ingredient-library-constant-crosscheck.v1"
c1 = diag["check1_dgeba_eew_admissibility"]
solid = c1["solid_type1_epoxy_band"]
assert solid["band_g_per_eq"] == [450.0, 550.0]
assert solid["n_gap_zone_probes_now_rejected"] == 4
assert solid["catalog_baseline_admitted"] is True
for r in c1["per_constant"]:
    assert r["within_admissible_band"] is True

# original signed receipt being (partially, scoped) superseded must remain byte-identical
cc_receipt = CC_DIR / "constant-crosscheck-receipt.v1.dsse.json"
cc_sha_now = sha(cc_receipt.read_bytes())
CC_SHA_EXPECTED = "85b207a9f5d0c2d07b1d2b78c8635250d8d29cd3402ff2ce546942f61d28a50f"
assert cc_sha_now == CC_SHA_EXPECTED, "superseded receipt was modified!"

# R-A01's prior (diagnostic-only) repair receipt must also remain byte-identical
ra01_sha_now = sha(RA01_DONE.read_bytes())

# refuting receipt bytes re-read here (not from prompt) to confirm the TDS band
refuting_bytes = REFUTING.read_bytes()
refuting_sha = sha(refuting_bytes)
refuting_payload = json.loads(base64.b64decode(json.loads(refuting_bytes)["signature"]["payload"]))
tds_band = refuting_payload["results"]["band_width_comparison"]["true_manufacturer_tds_band_g_per_eq"]
assert tds_band == [450.0, 550.0], tds_band
probe_vals = sorted(p["probe_eew_g_per_eq"] for p in refuting_payload["results"]["mutation_replay"]["probe_values"])
assert probe_vals == [400.0, 420.0, 600.0, 650.0], probe_vals

facts_sha = diag["inputs"]["facts_json_sha256"]
FACTS_SHA_EXPECTED = "0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb"
assert facts_sha == FACTS_SHA_EXPECTED, "facts.json changed since the refuting receipt was signed"

harness_sha = sha(script_path.read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
assert eval_key_id.startswith("phase0-evaluator-3ef6b35"), eval_key_id
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key not pinned in phase0 trust store"


def build_payload():
    return {
        "schema": "amphora.ingredient-library.repair-V1-ING-done-receipt.v1",
        "receipt_id": "repair-V1-ING-done",
        "module_id": "amphora-ingredient-library",
        "repair_item": "V1-ING",
        "repair_mode": "cron-2026-08-04",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "phase": "PRE_PHASE_0",
        "date": "2026-08-04",
        "generated_on_host": "xbabe2",
        "objective": "Land the TDS-correct solid_type1_epoxy EEW admissibility band "
                     "in the LIVE constant-crosscheck-v1 oracle (not merely a repair-time "
                     "diagnostic) and re-run the real check end-to-end to confirm the 4 "
                     "gap-zone probes now reject while the real catalog value still passes.",
        "prior_repair_gap": {
            "prior_receipt": str(RA01_DONE.relative_to(ROOT)),
            "prior_receipt_sha256": ra01_sha_now,
            "gap_found": "R-A01's defect2_corrected_values block computed the correct TDS "
                         "band and re-attack numbers, but only inside its own repair "
                         "diagnostic (work/run_repair_ra01.py); it did NOT edit the LIVE "
                         "oracle source. At the start of this fire, "
                         "evidence/audit/constant-crosscheck-v1/run_crosscheck.py still "
                         "contained the refuted predicate 'admissible = 1.5 <= n <= 3.5' "
                         "(EEW band [383.5, 667.8]), verified by direct grep/read of the "
                         "live file (sha256 %s) before any edit this fire." % SHA_BEFORE,
        },
        "live_code_fix": {
            "file": "amphora-ingredient-library/evidence/audit/constant-crosscheck-v1/run_crosscheck.py",
            "sha256_before": SHA_BEFORE,
            "sha256_after": script_sha_after,
            "change": "solid_type1_epoxy admissibility predicate replaced from the invented "
                      "n in [1.5,3.5] window (EEW [383.5,667.8]) with the Hexion HCD-4022 "
                      "manufacturer TDS band EEW [450.0,550.0] g/eq, read from the refuting "
                      "receipt's own signed payload bytes "
                      "(results.band_width_comparison.true_manufacturer_tds_band_g_per_eq), "
                      "not from any prompt text. Also added a solid-band fail-closed "
                      "mutation demo replaying the refuting receipt's own 4 gap-zone probe "
                      "values, and corrected the module's non_circularity/theory_reference/"
                      "headline prose to stop describing the solid band as structure-derived "
                      "(it is single-source manufacturer TDS, honestly labeled as such). The "
                      "liquid_DGEBA sub-check, Check-2 densities, pigment diagnostic and AHEW "
                      "honest-negative are untouched.",
        },
        "refuting_receipt_reverified": {
            "path": str(REFUTING.relative_to(ROOT)),
            "sha256": refuting_sha,
            "tds_band_g_per_eq_read_from_payload_bytes": tds_band,
            "gap_zone_probe_values_read_from_payload_bytes": probe_vals,
        },
        "live_rerun": {
            "command": "python3 run_crosscheck.py --emit <workdir>/diagnostic.run{A,B}.json, "
                       "run twice as independent OS processes under flock on .cron.lock",
            "facts_json_sha256": facts_sha,
            "run1_sha256": diag_sha,
            "run2_sha256": sha(runB),
            "two_replay_gate": "PASS",
            "byte_identical": runA == runB,
            "results": {
                "catalog_value_g_per_eq": next(
                    r["catalog_eew_g_per_eq"] for r in c1["per_constant"]
                    if r["constant"] == "resin.solid_cut_1001x75.eew_on_nv"),
                "catalog_value_within_tds_band": solid["catalog_baseline_admitted"],
                "tds_band_g_per_eq_in_force": solid["band_g_per_eq"],
                "n_gap_zone_probes_rejected": solid["n_gap_zone_probes_now_rejected"],
                "gap_zone_mutation_demo": solid["fail_closed_mutation_demo"],
                "liquid_dgeba_subcheck_unaffected": all(
                    r["within_admissible_band"] for r in c1["per_constant"]
                    if r["resin_class"] == "liquid_DGEBA"),
                "check2_density_all_within_gate": diag["check2_density_second_source"]["all_within_gate"],
            },
        },
        "reattack_of_original_refutation": {
            "method": "The refuting receipt's own 4 probe EEW values (re-read from its signed "
                      "payload bytes this fire, not transcribed from the prompt) replayed "
                      "against the LIVE corrected admissibility predicate via a real "
                      "end-to-end re-run of run_crosscheck.py (not a standalone diagnostic "
                      "script).",
            "n_probes_demonstrating_missed_detection_originally": 4,
            "n_probes_now_rejected": solid["n_gap_zone_probes_now_rejected"],
            "all_previously_undetected_probes_now_rejected": solid["n_gap_zone_probes_now_rejected"] == 4,
            "catalog_value_still_admitted": solid["catalog_baseline_admitted"],
        },
        "headline": "V1-ING lands the R-A01-computed TDS band [450.0, 550.0] g/eq in the LIVE "
                    "constant-crosscheck-v1 oracle (run_crosscheck.py sha256 %s -> %s) and "
                    "re-runs it end-to-end twice (byte-identical): the real catalog value "
                    "500.0 g/eq passes, and all 4 gap-zone probes from the original refuting "
                    "receipt (400/420/600/650 g/eq) are now rejected. R-A01's fix had only "
                    "existed inside a repair-time diagnostic; it never reached the live "
                    "oracle before this fire." % (SHA_BEFORE, script_sha_after),
        "closes": [
            "constant-crosscheck-v1 Check-1 solid_type1_epoxy sub-check now runs the TDS "
            "band in its LIVE code path (not just a repair diagnostic); reattack of the "
            "original refuting receipt's 4 gap-zone probes confirms 4/4 now rejected.",
        ],
        "does_not_close": [
            "Does not establish product qualification, wet-lab performance, or supplier closure.",
            "The corrected solid band remains single-source (manufacturer TDS); no independent "
            "second physical source for the solid cut is claimed, consistent with facts.json's "
            "own single_source_waiver.",
            "Does not re-audit Check-2 densities, the pigment diagnostic, or the polyamide AHEW "
            "honest-negative; those sub-checks are unmodified.",
            "Does not modify facts.json, any prior signed receipt, the falsification ledger, "
            "the module manifest, or the master portfolio manifest.",
        ],
        "modifies_existing_receipts": False,
        "modifies_manifest": False,
        "modifies_module_manifest": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "trust_anchored_in_phase0_store": True,
        "supersedes": {
            "superseded_path": str(cc_receipt.relative_to(ROOT)),
            "superseded_sha256": cc_sha_now,
            "superseded_deleted_or_modified": False,
            "reason": "constant-crosscheck-v1 Check-1's solid_type1_epoxy EEW admissibility "
                      "band [383.5, 667.8] g/eq (n in [1.5, 3.5]) was refuted 2026-08-03T14:06 "
                      "by eew-solid-band-mislabel-gap-v1 (2.84x wider than the manufacturer "
                      "TDS band; 4/4 gap-zone probes undetected). R-A01 (2026-08-03) computed "
                      "the correct repair but only inside a standalone repair diagnostic; the "
                      "LIVE oracle code was unchanged. This receipt supersedes that sub-check "
                      "for real: the live run_crosscheck.py now enforces the TDS band "
                      "[450.0, 550.0] g/eq and was re-run end-to-end (not just recomputed in "
                      "a diagnostic) to confirm the fix. The original signed receipt remains "
                      "in place, unmodified, for the audit trail. Scope: supersedes ONLY the "
                      "solid_type1_epoxy sub-check of Check-1; the liquid-DGEBA sub-check, "
                      "Check-2 densities, pigment diagnostic and AHEW honest-negative are NOT "
                      "superseded.",
        },
        "reproducibility": {
            "two_replay_sha256_gate": "PASS",
            "live_rerun_run1_sha256": diag_sha,
            "live_rerun_run2_sha256": sha(runB),
            "byte_identical": runA == runB,
            "replay_method": "run_crosscheck.py (corrected) executed twice as independent "
                             "python3 OS processes, each with an internal two-replay "
                             "byte-stability self-check (build() called twice, asserted "
                             "equal), emitting canonical json.dumps(sort_keys=True,indent=2) "
                             "bytes to diagnostic.runA.json / diagnostic.runB.json; both "
                             "files are byte-identical.",
        },
        "provenance": {
            "harness_sha256": {
                "evidence/audit/constant-crosscheck-v1/run_crosscheck.py": harness_sha,
            },
            "superseded_receipt_sha256_verified_intact_at_signing": cc_sha_now,
            "ra01_done_receipt_sha256_verified_intact_at_signing": ra01_sha_now,
            "refuting_receipt_sha256_verified_intact_at_signing": refuting_sha,
        },
        "signing_key": {
            "role": "PHASE0_EVALUATOR",
            "key_id": eval_key_id,
            "public_key_hex": eval_pub_hex,
            "used_for": "AUDIT_ONLY repair done-receipt under evidence/phase0/repairs/",
            "signs_phase0_evaluation_or_review": False,
            "derives_pinned_trust_store_key_id": bool(eval_pin),
        },
        "reviewer_reference": {
            "role": "PHASE0_INTERNAL_REVIEWER",
            "key_id": rev_key_id,
            "public_key_hex": rev_pub_hex,
            "derives_pinned_trust_store_key_id": bool(rev_pin),
            "reviewer_signature_present": False,
            "note": "Reviewer key referenced for provenance only; no independent "
                    "human review performed.",
        },
    }


# two-replay gate on the signed payload itself
body1 = json.dumps(build_payload(), sort_keys=True, separators=(",", ":")).encode()
body2 = json.dumps(build_payload(), sort_keys=True, separators=(",", ":")).encode()
assert body1 == body2, "payload two-replay bytes differ"
body = body1
ptype = "application/vnd.amphora.ingredient-library-repair-v1-ing-done-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "repair-V1-ING-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# ---- SELF-VERIFY (rebuild PAE from disk bytes, verify signature) ----------
reloaded = json.loads(out.read_bytes())
env2 = reloaded["signature"]
assert env2["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35"), \
    env2["signatures"][0]["keyid"]
pub_from_seed = Ed25519PrivateKey.from_private_bytes(
    load_seed(EVAL_SEED)).public_key().public_bytes_raw()
Ed25519PublicKey.from_public_bytes(pub_from_seed).verify(
    base64.standard_b64decode(env2["signatures"][0]["sig"]),
    pae(env2["payloadType"], base64.standard_b64decode(env2["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("live_rerun_sha256", diag_sha)
print("payload_sha256", sha(body))
print("receipt_sha256", sha(out.read_bytes()))
print("signature_self_verified_from_disk", True)
