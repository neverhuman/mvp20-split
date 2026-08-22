#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-cro-protocol-packager CF-PROC mixing/
induction/application/bench-scale crosswalk audit receipt (campaign item
CF-PROC, founder directive AMPHORA-DIRECTIVE-2026-08-09 S7, obligation
CF-PROC, max_fires=2, fire 1/2).

AUDIT_ONLY. Crosswalks the envelope's own process/application requirements
(amphora-envelope-gates/reference/mvp20/charter/v5_requirements.json)
against the CF-PROC deliverable corpus (amphora-report-packager's
blueprint.md Section 2 + surrounding process prose, and this module's own
cro_protocol.md / capture_template.json). Finds 5 genuinely missing
parameters (CLAIM_REFUTED), with a positive control (attack-shape-literal:
strip induction-time from a copy) and a discrimination control (synthetic
fully-patched copy) both passing. Filed into
evidence/phase0/repairs/CF-PROC/attempts/ (NOT done/ -- the deliverable is
not complete; the gaps live in blueprint.md, owned by amphora-report-
packager, outside this fire's write scope).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-cro-protocol-packager/evidence/audit/cf-proc-mixing-induction-application-crosswalk-v1"
ATTEMPTS_DIR = ROOT / "amphora-cro-protocol-packager/evidence/phase0/repairs/CF-PROC/attempts"
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
assert diag["verdict"] == "CLAIM_REFUTED"
assert diag["step_b_positive_control"]["detected"] is True
assert diag["step_c_discrimination_control"]["discrimination_control_passed"] is True
harness_sha = sha((BENCH / "run_cf_proc_crosswalk_audit.py").read_bytes())

# --- derive public key / key_id from on-host seed ---------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))

missing = diag["step_a_real_crosswalk"]["missing_keys"]
missing_detail = [p for p in diag["step_a_real_crosswalk"]["params"] if p["key"] in missing]

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.cro-protocol-packager.cf-proc-mixing-induction-application-crosswalk-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "module": "amphora-cro-protocol-packager",
    "campaign_item_id": "CF-PROC",
    "run_type": "falsification_attack",
    "fire_sequence": 1,
    "final_fire_for_item": False,
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
    "envelope_source": diag["envelope_source"],
    "refutation_criterion_verbatim": diag["refutation_criterion_verbatim"],
    "refutation_criterion_observed": (
        "OBSERVED: the mixing, induction and application section (blueprint.md "
        "Section 2 'Manufacturing process' plus its surrounding process prose "
        "in Sections 1/8 and the Q1-Q15 answers, cross-read with this module's "
        "own cro_protocol.md batch-record/application tables and "
        "capture_template.json) omits 5 parameters the envelope's own WFT, "
        "coverage or cure schedule requires: dry_to_touch_h (2 h functional "
        "target -- only the differing MIL-cited 3 h set-to-touch number "
        "appears), functional_cure_h (6 h functional target, never stated as "
        "such), recoat_window_h (6 h target, never stated), the mix ratio's "
        "own 3% engine_tolerance_pct (the 1:1 ratio is stated but its "
        "tolerance band is not), and a numeric thinning limit (the done_"
        "criteria names 'thinning limits' verbatim; the deliverable only "
        "carries qualitative language -- 'thinner discipline', 'unapproved "
        "thinning' -- with no stated %, fl oz/gal, or other numeric cap). "
        "The scale-sensitive-step clause of the criterion does NOT fire: Q2 "
        "explicitly flags dispersion heat, tip speed, and grind temperature "
        "as scale-sensitive for the pilot path. So the refutation rests on "
        "the WFT/coverage/cure-schedule clause, which fired 5 times over."
    ),
    "attack_shape_verbatim": diag["attack_shape_verbatim"],
    "step_a_real_crosswalk": diag["step_a_real_crosswalk"],
    "step_b_positive_control": diag["step_b_positive_control"],
    "step_c_discrimination_control": diag["step_c_discrimination_control"],
    "finding": (
        "CLAIM_REFUTED. Crosswalking the envelope's own process/application "
        "requirements (amphora-envelope-gates/reference/mvp20/charter/"
        "v5_requirements.json performance_envelope + fixed_constraints) "
        "against the CF-PROC deliverable corpus (blueprint.md Section 2 + "
        "process prose, cro_protocol.md, capture_template.json) finds 5 of "
        "10 audited parameters missing: " + ", ".join(missing) + ". Two of "
        "these (dry_to_touch_h, functional_cure_h) are cure-schedule targets "
        "the envelope itself declares that the deliverable never states -- "
        "the deliverable only carries the differently-valued MIL-spec-cited "
        "numbers (set-to-touch 3 h vs the envelope's own dry-to-touch 2 h "
        "target), which is exactly the WFT/coverage/cure-schedule omission "
        "the refutation criterion names. recoat_window_h (6 h) is likewise "
        "absent. The mix ratio's own 3% engine tolerance band is stated "
        "nowhere, and 'thinning limits' -- named verbatim in the CF-PROC "
        "done_criteria -- has no numeric instantiation anywhere in the "
        "corpus, only qualitative language ('thinner discipline', "
        "'unapproved thinning'). Positive control (attack-shape-literal: "
        "stripped every induction-time-with-value mention and bare "
        "'induction' token from a copy of the full corpus) confirms the "
        "crosswalk correctly flips induction_min from found to missing "
        "(detected=True), proving the checker fires on the attack shape's "
        "own worked example. Discrimination control (a synthetic "
        "fully-patched copy stating explicit dry-to-touch/functional-cure/"
        "recoat/mix-ratio-tolerance/thinning-limit language) confirms the "
        "SAME checker reports zero of the 5 previously-missing keys as still "
        "missing (discrimination_control_passed=True, "
        "still_missing_after_patch=[]) -- the checker genuinely "
        "discriminates rather than being hard-wired to always refute or "
        "always survive."
    ),
    "verdict": "CLAIM_REFUTED",
    "repair_status": "not_started",
    "campaign_item_status": "pending",
    "campaign_item_disposition": (
        "Fire 1/2 for CF-PROC. This fire only attacks and documents; it does "
        "not repair. The 5 missing parameters live in blueprint.md Section 2 "
        "and its surrounding process prose, which is owned by "
        "amphora-report-packager, outside this fire's amphora-cro-protocol-"
        "packager write-scope confinement (the same structural pattern the "
        "sibling CF-BOM item hit against the same file). No external data is "
        "required to repair this -- all 5 missing values already exist in "
        "amphora-envelope-gates' v5_requirements.json and only need to be "
        "quoted into the deliverable's process/application section, plus a "
        "derived numeric thinning limit stated explicitly (e.g. from the VOC "
        "design-to/max headroom). A future amphora-report-packager-scoped "
        "fire (or a cross-module exception) should add this language to "
        "blueprint.md Section 2 (and/or Section 1's acceptance table), after "
        "which a future amphora-cro-protocol-packager fire should re-run this "
        "checker (script sha256 below) as the acceptance test before writing "
        "to done/."
    ),
    "does_not_close": (
        "This receipt does not repair the CF-PROC deliverable and does not "
        "assert CLAIM_SURVIVED. It documents a genuine, reproducible "
        "completeness gap against the envelope's own process requirements, "
        "with a positive control proving the checker detects the attack "
        "shape's own worked defect and a discrimination control proving the "
        "checker is not hard-wired to always refute."
    ),
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "diagnostic_script_sha256": harness_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/ and evidence/phase0/repairs/CF-PROC/attempts/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.cro-protocol-packager-cf-proc-mixing-induction-application-crosswalk+json"
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

out = BENCH / "cf-proc-mixing-induction-application-crosswalk-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

ATTEMPTS_DIR.mkdir(parents=True, exist_ok=True)
attempts_out = ATTEMPTS_DIR / "cf-proc-mixing-induction-application-crosswalk-receipt.v1.dsse.json"
attempts_out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify -------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))
pk.verify(base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(json.loads(attempts_out.read_text())["signature"]["payload"])))

print("WROTE", out)
print("WROTE", attempts_out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
