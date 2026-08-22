#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-ALT repair
receipt (campaign item CF-ALT, founder directive AMPHORA-DIRECTIVE-2026-08-09
S7, obligation CF-ALT, max_fires=2, fire 2/2 FINAL -- REPAIR-MODE re-attack).

AUDIT_ONLY. Repairs the fire-1-refuted gap (evidence-indistinguishable
M00097/M00101/M00109 pairs shipped with no discriminating experiment keyed
to them) by adding, within this module's own write scope,
candidate_ranking (primary + ranked_alternates) and
candidate_pairwise_discriminating_experiments to
reference/mvp20/out/capture_template.json. Re-attacks with a v2 checker
whose core evidence_indistinguishable()/all_pairs()/find_unresolved()
logic is byte-identical to fire 1's v1 checker; the resolution lookup was
changed from v1's hardcoded {} (an audit snapshot, not a live check) to a
live derivation off the new corpus field, since re-running v1 byte-for-byte
could never observe any repair. v2 regression-checks itself against the
saved pre-repair snapshot (reproduces fire 1's exact finding) before
declaring the live acceptance test.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-alt-ranked-alternates-discriminating-experiment-v2"
DONE_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-ALT/done"
ATTEMPTS_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-ALT/attempts"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(path):
    raw = path.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


# --- two-replay gate --------------------------------------------------------
canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
assert diag["verdict"] == "CLAIM_SURVIVED"
assert diag["step_a_regression_against_pre_repair_snapshot"]["matches_fire1_finding"] is True
assert diag["step_b_live_repaired_acceptance_test"]["repair_holds"] is True
assert diag["step_c_positive_control"]["detected"] is True
harness_sha = sha((BENCH / "run_cf_alt_alternates_audit_v2.py").read_bytes())
v1_harness_path = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-alt-ranked-alternates-discriminating-experiment-v1/run_cf_alt_alternates_audit_v1.py"
v1_harness_sha = sha(v1_harness_path.read_bytes())

# --- derive public key / key_id from on-host seed ---------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.cf-alt-ranked-alternates-discriminating-experiment-repair-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-ALT",
    "run_type": "repair_reattack",
    "fire_sequence": 2,
    "final_fire_for_item": True,
    "directive_path": diag["directive_path"],
    "directive_sha256": diag["directive_sha256"],
    "directive_obligation": diag["directive_obligation"],
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "modifies_mission_front_matter": False,
    "modifies_mission_prose": False,
    "claim_under_attack": diag["claim_under_attack"],
    "deliverable_under_test": diag["deliverable_under_test"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "attack_shape_verbatim": diag["attack_shape_verbatim"],
    "refutation_criterion_observed_this_fire": (
        "NOT OBSERVED on the live (repaired) corpus: all three evidence-"
        "indistinguishable pairs among M00097/M00101/M00109 now carry both "
        "(a) a stated primary + ranked alternates (candidate_ranking: "
        "primary=M00097, ranked_alternates=[M00101, M00109], ordered by "
        "ascending |pvc_pct - primary.pvc_pct|) and (b) a pair-keyed named "
        "discriminating experiment (candidate_pairwise_discriminating_"
        "experiments), directly in the M00-series id namespace this "
        "module's own candidates/prediction_ledger use. The criterion WAS "
        "observed (and correctly re-derived) on the saved pre-repair "
        "snapshot, and fires correctly again the instant one pair's "
        "resolution is stripped (positive control)."
    ),
    "prior_fire_finding": (
        "Fire 1 (20260811T030001-523942-cc6bad6ad57c) found all 3 pairs "
        "among M00097/M00101/M00109 evidence-indistinguishable by the "
        "corpus's own tier labels, with the corpus's one named "
        "discriminating experiment (key_pairwise: Enhanced-65 > "
        "Envelope-65) keyed to an uncross-walked track-name namespace, "
        "leaving 0 of 3 pairs resolvable by M00-series id. Receipt: "
        "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-ALT/"
        "attempts/cf-alt-ranked-alternates-discriminating-experiment-audit-"
        "receipt.v1.dsse.json."
    ),
    "repair_applied": {
        "write_scope": "amphora-cro-protocol-packager only (this module's own reference/mvp20/out/capture_template.json)",
        "file_changed": "amphora-cro-protocol-packager/reference/mvp20/out/capture_template.json",
        "pre_repair_sha256": diag["pre_repair_snapshot_sha256"],
        "post_repair_sha256": diag["live_capture_template_sha256"],
        "pre_repair_snapshot_path": "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-ALT/work/pre_repair_capture_template.snapshot.json",
        "fields_added": [
            "candidate_ranking (primary=M00097, ranked_alternates=[M00101, M00109], objective distance-from-primary ranking rule stated in-file, asserts no corrosion-performance ordering)",
            "candidate_pairwise_discriminating_experiments (pair-keyed entries for all 3 pairs: M00097|M00101, M00097|M00109, M00101|M00109; each names the discriminating experiment by reusing this file's own already-defined decision_experiment.minimum_design + acceptance_gates/early_kill_gates protocol and statistical_decision_rules.minimum_detectable_effect/tie_rule decision threshold, extended to carry the M00-series candidates as explicit arms; status is NAMED, not yet executed -- CRO execution remains an external dependency per docs/mission.md, and this repair claims no new measured result)",
        ],
        "scope_note": (
            "The repair sidesteps the separate, still-open cross-module "
            "question (also flagged by fire 1) of whether/how M00101 and "
            "M00109 map onto the Lineage-60/Envelope-65/Enhanced-65/"
            "CRO-Robust-65 track-name namespace used by statistical_"
            "decision_rules and amphora-report-packager's blueprint.md. "
            "CF-ALT's refutation criterion requires a named discriminating "
            "experiment per evidence-indistinguishable pair -- it does not "
            "require that cross-module crosswalk, so naming the "
            "experiments directly in the M00-id namespace is a complete, "
            "honest closure of THIS criterion. A separate, still-open "
            "residual finding (out of CF-ALT's scope): M00098 (blueprint's "
            "'functional variant', plausibly = Enhanced-65) remains absent "
            "from this module's own candidates list and prediction_ledger "
            "-- an internal bookkeeping question independent of the "
            "ranked-alternates/discriminating-experiment criterion, not "
            "resolved by or blocking this repair."
        ),
    },
    "reattack_methodology": (
        "v2 checker (evidence/audit/cf-alt-ranked-alternates-discriminating-"
        "experiment-v2/run_cf_alt_alternates_audit_v2.py) reuses v1's "
        "evidence_indistinguishable()/all_pairs()/find_unresolved() "
        "functions and thresholds byte-for-byte (copy-paste, unchanged). "
        "v1's real_resolved_pair_experiments was a manually-asserted empty "
        "dict, an audit snapshot rather than a live check, so re-running "
        "v1 byte-for-byte could never observe any repair regardless of "
        "corpus changes -- v2's only change is deriving that dict LIVE "
        "from the new candidate_pairwise_discriminating_experiments field, "
        "plus a new candidate_ranking validity check v1 did not perform at "
        "all. v1 harness sha256 (unchanged, cited not re-run): "
        + v1_harness_sha + ". v2 harness sha256: " + harness_sha + "."
    ),
    "step_a_regression_against_pre_repair_snapshot": diag["step_a_regression_against_pre_repair_snapshot"],
    "step_b_live_repaired_acceptance_test": diag["step_b_live_repaired_acceptance_test"],
    "step_c_positive_control": diag["step_c_positive_control"],
    "finding": (
        "CLAIM_SURVIVED (repaired). Step A confirms v2's derivation logic, "
        "run against the untouched pre-repair snapshot, reproduces fire "
        "1's exact finding byte-for-byte in substance (3/3 pairs "
        "unresolved, no ranking field present) -- proving v2 generalizes "
        "v1 rather than being gerrymandered to only pass on the repaired "
        "file. Step B (the live acceptance test) shows all 3 evidence-"
        "indistinguishable pairs now resolve (n_unresolved=0) and "
        "candidate_ranking validly partitions the 3 candidates into a "
        "primary + 2 ranked alternates. Step C (positive control, attack-"
        "shape-literal: stripping the M00101-vs-M00109 resolution from a "
        "copy, i.e. 'merge two curative alternates into one unexplained "
        "pick') re-flags exactly that pair and only that pair "
        "(detected=True) -- the checker is not hard-wired to always "
        "survive; it genuinely discriminates a re-introduced defect."
    ),
    "verdict": "CLAIM_SURVIVED",
    "repair_status": "fix_landed_survived",
    "campaign_item_status": "done",
    "campaign_item_disposition": (
        "Fire 2/2 (final, max_fires exhausted) for CF-ALT. The within-"
        "module-write-scope repair fully closes the pre-committed "
        "refutation criterion for all 3 evidence-indistinguishable pairs "
        "among this module's own carried candidates. The residual M00098/"
        "Enhanced-65 bookkeeping gap and the M00-id<->track-name crosswalk "
        "question remain open but are outside CF-ALT's pre-committed "
        "criterion and are not repair-blocking for this item."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "v2_diagnostic_script_sha256": harness_sha,
        "v1_diagnostic_script_sha256_cited_unchanged": v1_harness_sha,
    },
    "supersedes": None,
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair receipt under evidence/audit/ and evidence/phase0/repairs/CF-ALT/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-alt-ranked-alternates-discriminating-experiment-repair+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

out = BENCH / "cf-alt-ranked-alternates-discriminating-experiment-repair-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

DONE_DIR.mkdir(parents=True, exist_ok=True)
done_out = DONE_DIR / "cf-alt-ranked-alternates-discriminating-experiment-repair-receipt.v1.dsse.json"
done_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(done_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", done_out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
