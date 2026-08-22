#!/usr/bin/env python3
"""DSSE-Ed25519-sign the X-LEDGER-TS parser-guard repair receipt (CAMPAIGN item
X-LEDGER-TS, module amphora-redteam-audit, directive AMPHORA-DIRECTIVE-2026-08-05
A.3). AUDIT_ONLY. Does not modify the master manifest or any locked dataset.
The ledger itself is asserted byte-identical before and after this fire.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/X-LEDGER-TS/work"
OUT_DIR = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/X-LEDGER-TS/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
LEDGER = ROOT / "logs/falsification-ledger.jsonl"
GUARD = ROOT / "amphora-redteam-audit/src/amphora_redteam_audit/ledger_ts.py"
GUARD_INIT = ROOT / "amphora-redteam-audit/src/amphora_redteam_audit/__init__.py"
TEST = ROOT / "amphora-redteam-audit/tests/test_ledger_ts.py"
CONSUMER = ROOT / "reports/portfolio-status-2026-08-03/scripts/04_render_snippets.py"

FIRE_ID = "20260814T090001-97736-fadee5ac7e01"
DIRECTIVE_PATH = "docs/directives/2026-08-05-closing-the-open-portfolio.md"
DIRECTIVE_SHA256 = "dcedb048e1142529de84aa6d741a065fdc29ebf744ef1b2feb81951c74573a6d"

LEDGER_SHA256_PINNED_BEFORE = "3cd5276e036ba9d3d193cd894bdb93f566f5050f01d861407b4050de1bd7b2ec"
CONSUMER_SHA256_BEFORE = "cfe33fba1633703a2c5e299cb342f321c828f06fe69ba602494e1740f49612b8"


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


ledger_bytes = LEDGER.read_bytes()
ledger_sha_now = sha(ledger_bytes)
assert ledger_sha_now == LEDGER_SHA256_PINNED_BEFORE, (
    "ledger changed since the pre-fire snapshot was taken -- append-only violation "
    f"or unrelated concurrent append: {ledger_sha_now} != {LEDGER_SHA256_PINNED_BEFORE}"
)

runA_bytes = (WORK / "diagnostic.runA.json").read_bytes()
runB_bytes = (WORK / "diagnostic.runB.json").read_bytes()
byte_identical = runA_bytes == runB_bytes
assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"
diag = json.loads(runA_bytes)
assert all(v == "PASS" for v in diag.values()), diag
canon_sha = sha(runA_bytes)

guard_sha = sha(GUARD.read_bytes())
test_sha = sha(TEST.read_bytes())
consumer_sha_after = sha(CONSUMER.read_bytes())

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
assert eval_pin, "evaluator key_id does not match pinned trust store"

consumer_enumeration = [
    {
        "path": "reports/portfolio-status-2026-08-03/scripts/04_render_snippets.py",
        "parses_ledger_ts": True,
        "pre_fire_behavior": "bare datetime.fromisoformat(v['ts'].replace('Z','+00:00')) "
                              "(raises ValueError on either real corrupt row) and "
                              "sorted(vs, key=lambda x: x['ts']) (raw-string sort puts both "
                              "corrupt rows after every normal row, since '\\\\' > every ASCII "
                              "digit, regardless of true chronological position)",
        "status": "FIXED_THIS_FIRE",
        "fix": "imports amphora_redteam_audit.ledger_ts (parse_ledger_ts, ledger_sort_key) "
               "and uses them in place of the bare call and the raw-string sort key",
        "sha256_before": CONSUMER_SHA256_BEFORE,
        "sha256_after": consumer_sha_after,
        "note": "This report's own data/ledger.jsonl snapshot (54 lines, pulled "
                "2026-08-03) predates both corrupt rows (ledger lines 56, 75) so it is "
                "not currently exposed, but the code path is genuinely unsafe against "
                "the live ledger and was fixed for that reason. Verified post-fix: "
                "importing the guard and running parse_ledger_ts/ledger_sort_key over "
                "the live 222-line ledger correctly parses and orders both real corrupt "
                "rows (see reproducibility.live_ledger_smoke_test below). The script's "
                "own ROOT constant points outside this checkout "
                "(/home/ubuntu/amphora/reports/...), a pre-existing condition unrelated "
                "to this fix, so a full end-to-end run was not possible in this "
                "environment; py_compile and the import+parse+sort smoke test both pass.",
    },
    {
        "path": "amphora-redteam-audit/evidence/phase0/repairs/U-PROSE/work/run_prose_sweep.py",
        "parses_ledger_ts": True,
        "pre_fire_behavior": "reads rec.get('ts') per ledger line and copies it verbatim "
                              "into an output record; never parsed as a datetime or used "
                              "as a sort key",
        "status": "ALREADY_TOLERANT",
        "fix": "none needed",
    },
    {
        "path": "amphora-ip-fto-guard/evidence/phase0/repairs/R-A13/work/repair_r_a13.py",
        "parses_ledger_ts": True,
        "pre_fire_behavior": "asserts ledger line 56's ts equals the known corrupted "
                              "constant CORRUPTED_TS = '\\\\' + '2026-08-03T15:08:37+00:00' "
                              "by design (the script exists specifically to document this "
                              "row's erratum) and embeds a ledger_erratum block "
                              "(corrected_value) in its own already-signed done/ receipt",
        "status": "ALREADY_TOLERANT_BY_DESIGN",
        "fix": "none needed; frozen historical repair script, already executed and signed "
               "(amphora-ip-fto-guard/evidence/phase0/repairs/R-A13/done/"
               "claim-chart-supersede-repair.R-A13.v1.dsse.json), covers ledger line 56 only "
               "(not line 75) and is not a general reusable read path",
    },
    {
        "path": "reports/portfolio-status-2026-08-03/scripts/03_figures.py",
        "parses_ledger_ts": False,
        "pre_fire_behavior": "parses ts from data/fire_summary.jsonl records (a distinct "
                              "file, not the falsification ledger), already inside a "
                              "try/except that skips unparseable rows",
        "status": "NOT_A_LEDGER_TS_CONSUMER",
        "fix": "none needed; different data source, and already defensive regardless",
    },
]

n_files_grepped_referencing_ledger_path = 19
n_real_ts_field_consumers = len(consumer_enumeration)

body_obj = {
    "schema": "amphora.redteam-audit.x-ledger-ts-parser-guard-repair-receipt.v1",
    "receipt_id": "x-ledger-ts-parser-guard-repair-v1",
    "authority": "AUDIT_ONLY",
    "run_type": "REPAIR",
    "module": "amphora-redteam-audit",
    "campaign_item_id": "X-LEDGER-TS",
    "fire_id": FIRE_ID,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_other_module_files": True,
    "modifies_other_module_files_detail": (
        "reports/portfolio-status-2026-08-03/scripts/04_render_snippets.py is not owned "
        "by any single module (it lives under the shared top-level reports/ tree, is a "
        "stale one-off report generator last touched 2026-08-03, and its own ROOT constant "
        "points outside this checkout entirely). It was patched with a minimal 4-line diff "
        "(import + 2 call-site substitutions) to close the one genuinely unsafe ledger-ts "
        "consumer found by the sweep below; full diff and before/after sha256 recorded in "
        "reproducibility.consumer_patch_diff."
    ),
    "directive_path": DIRECTIVE_PATH,
    "directive_sha256": DIRECTIVE_SHA256,
    "directive_obligation": "X-LEDGER-TS",
    "directive_obligation_text": {
        "title": "Ship and prove the leading-backslash timestamp parser guard",
        "done_criteria": "The append-only rows stay; the read path must tolerate them; "
                          "regression test included.",
        "source": "docs/directives/2026-08-05-closing-the-open-portfolio.index.json#X-LEDGER-TS",
    },
    "claim_under_attack": "Every consumer of the falsification ledger reads the two "
                           "corrupt-ts rows correctly.",
    "attack_description": (
        "Enumerated every file in the tree referencing 'falsification-ledger' "
        f"({n_files_grepped_referencing_ledger_path} files, excluding logs/cron-audit "
        "snapshots and .git internals), then narrowed to files that actually extract and "
        "use the ledger's `ts` field (not merely the ledger path as a string) via grep for "
        "fromisoformat/strptime/dateutil/sort-on-ts patterns plus manual read of every hit. "
        f"Found {n_real_ts_field_consumers} real ts-field consumers. One "
        "(reports/.../04_render_snippets.py) called bare datetime.fromisoformat on the raw "
        "ts and sorted ledger rows by the raw ts string -- both fail/misorder on the two "
        "real corrupt rows (ledger lines 56, 75), which is exactly the claim's failure mode. "
        "The other two are already tolerant (one passes ts through untouched; one asserts "
        "the specific corrupted constant by design, as a frozen historical erratum note)."
    ),
    "consumer_enumeration": consumer_enumeration,
    "n_files_grepped_referencing_ledger_path": n_files_grepped_referencing_ledger_path,
    "n_real_ts_field_consumers": n_real_ts_field_consumers,
    "repair": {
        "guard_module": "amphora-redteam-audit/src/amphora_redteam_audit/ledger_ts.py",
        "guard_module_sha256": guard_sha,
        "guard_api": ["clean_ledger_ts(ts)", "parse_ledger_ts(ts)", "ledger_sort_key(record)"],
        "guard_module_is_importable_at": "amphora-redteam-audit/src (amphora_redteam_audit "
                                          "package; sys.path.insert used by the one external "
                                          "consumer patched this fire)",
        "regression_test": "amphora-redteam-audit/tests/test_ledger_ts.py",
        "regression_test_sha256": test_sha,
        "regression_test_built_from": "the two REAL corrupt rows read live from "
                                       "logs/falsification-ledger.jsonl by fire_id "
                                       "(20260803T150004-335042-88e86edf7333, "
                                       "20260804T100001-3937441-823cffd3f9d8), not synthetic "
                                       "fixtures",
        "regression_test_result": diag,
        "ledger_never_rewritten": True,
        "ledger_sha256_before": LEDGER_SHA256_PINNED_BEFORE,
        "ledger_sha256_after": ledger_sha_now,
        "ledger_byte_identical": ledger_sha_now == LEDGER_SHA256_PINNED_BEFORE,
    },
    "positive_control": {
        "planted_defect": "the ORIGINAL, real defect class: parsing a ledger row's ts with "
                           "bare datetime.fromisoformat instead of the guard (this is "
                           "literally what every unfixed consumer, incl. "
                           "04_render_snippets.py before this fire, did)",
        "how_planted": "test_naive_bare_parse_fails_on_real_corrupt_rows_positive_control "
                        "in amphora-redteam-audit/tests/test_ledger_ts.py feeds the two "
                        "REAL corrupt ts strings read live from the ledger "
                        "('\\\\2026-08-03T15:08:37+00:00', '\\\\2026-08-04T10:07:20+00:00') "
                        "straight into bare datetime.fromisoformat(...replace('Z','+00:00')), "
                        "with no guard applied -- i.e. the exact call site that stood in "
                        "04_render_snippets.py before the fix",
        "detected": True,
        "evidence": "both raw ts strings raise ValueError under bare fromisoformat (test "
                     "asserts the raise happens; the ledger_ts guard removes the leading "
                     "backslash first, so the same two real rows parse cleanly under "
                     "parse_ledger_ts -- see regression_test_result.test_guard_parses_real_"
                     "corrupt_rows_correctly and test_naive_bare_parse_fails_on_real_corrupt_"
                     "rows_positive_control, both PASS)",
    },
    "verdict": "CLAIM_SURVIVED",
    "repair_status": "fix_landed_survived",
    "interpretation": (
        "Pre-fire: CLAIM_REFUTED in effect for one real consumer "
        "(04_render_snippets.py) -- it did not read the two corrupt-ts rows correctly "
        "(would raise on the fromisoformat path and mis-sort on the sort path). "
        "Post-fire, current state: CLAIM_SURVIVED. All 3 real ledger-ts consumers found in "
        "the tree now read both real corrupt rows correctly -- 2 were already tolerant, 1 "
        "is fixed via the new amphora_redteam_audit.ledger_ts guard, verified against the "
        "live 222-line ledger (not just the frozen 54-line report snapshot) and against a "
        "positive control that reproduces the exact original failure mode on an unguarded "
        "parse. The ledger itself is confirmed byte-identical before and after "
        f"(sha256 {LEDGER_SHA256_PINNED_BEFORE})."
    ),
    "does_not_close": [
        "Whether other, not-yet-written future consumers will remember to import the "
        "guard rather than parsing ts directly -- this receipt ships the guard and fixes "
        "every consumer found by an exhaustive tree grep at this fire's snapshot, but "
        "cannot bind code that does not yet exist.",
        "04_render_snippets.py's unrelated pre-existing inability to execute end-to-end in "
        "this environment (its ROOT constant points outside this checkout) -- out of scope "
        "for this repair, not caused by this fix, and noted for the record only.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
        "canonical_diagnostic_sha256": canon_sha,
        "runA_diagnostic_sha256": sha(runA_bytes),
        "runB_diagnostic_sha256": sha(runB_bytes),
        "byte_identical": byte_identical,
        "test_harness_path": "amphora-redteam-audit/tests/test_ledger_ts.py",
        "test_harness_sha256": test_sha,
        "live_ledger_smoke_test": (
            "python3 -c import + sort(key=ledger_sort_key) + parse_ledger_ts over the live "
            "222-line logs/falsification-ledger.jsonl: both real corrupt fire_ids parse to "
            "2026-08-03T15:08:37+00:00 and 2026-08-04T10:07:20+00:00 respectively, run "
            "manually this fire outside the pytest harness as an independent check"
        ),
        "consumer_patch_diff": {
            "path": "reports/portfolio-status-2026-08-03/scripts/04_render_snippets.py",
            "sha256_before": CONSUMER_SHA256_BEFORE,
            "sha256_after": consumer_sha_after,
            "diff": (
                "+import sys\n"
                "+sys.path.insert(0, \"/home/ubuntu/amphora/build/mvp20-split/"
                "amphora-redteam-audit/src\")\n"
                "+from amphora_redteam_audit.ledger_ts import parse_ledger_ts, "
                "ledger_sort_key  # noqa: E402\n"
                "-        rf\"{esc(datetime.fromisoformat(v['ts'].replace('Z','+00:00'))."
                "strftime('%m-%d %H:%M'))} & ...\"\n"
                "-        for v in sorted(vs, key=lambda x: x['ts']))\n"
                "+        rf\"{esc(parse_ledger_ts(v['ts']).strftime('%m-%d %H:%M'))} & ...\"\n"
                "+        for v in sorted(vs, key=ledger_sort_key))"
            ),
            "py_compile_ok": True,
        },
        "determinism": "pure stdlib json/datetime/hashlib; no RNG, no model fitting, no "
                        "wall-clock embedded in the diagnostic body",
    },
    "toolchain": {"python": "3", "note": "stdlib json/hashlib/datetime only"},
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair receipt under evidence/phase0/repairs/X-LEDGER-TS/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-audit-x-ledger-ts-repair+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

OUT_DIR.mkdir(parents=True, exist_ok=True)
out = OUT_DIR / "x-ledger-ts-parser-guard-repair-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("verdict", body_obj["verdict"])
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", canon_sha)
print("ledger_byte_identical", body_obj["repair"]["ledger_byte_identical"])
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
