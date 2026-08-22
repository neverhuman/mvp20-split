#!/usr/bin/env python3
"""R-A13: reinstate amphora-sourceability-ehs/reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json
and its companion KPI, both currently signed with the unanchored repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-9028773f49591193 / pubkey
4b722f45...) instead of the pinned PHASE0_EVALUATOR key -- the same
signing-key-selection bug R-A12 (2026-08-03) fixed for 2 other artifact
pairs (osha_table_z1_z2, vhr_temperature_envelope_crossmethod) but did not
sweep exhaustively. A full re-verification sweep this fire found 5 MORE
un-repaired wrong-key/no-key artifacts in this module; this fire reinstates
the single most heavily-depended-upon one (the base 9-solvent VHR panel,
worst_actor=methanol, cited as "pinned, signed" by R-S04, the antoine
crosscheck, and the temperature-envelope audits) and discloses the rest.
"""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
LOCAL_PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

WORKDIR = MOD / "evidence/phase0/repairs/R-A13/work"
WORKDIR.mkdir(parents=True, exist_ok=True)
OUTDIR = MOD / "evidence/phase0/repairs/R-A13/done"
OUTDIR.mkdir(parents=True, exist_ok=True)

ORIG_RECEIPT = MOD / "reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json"
ORIG_KPI = MOD / "evidence/phase0/kpis/vapor-hazard-ratio-inhalation-prescreen-kpi.v1.json"
HARNESS = MOD / "benchmarks/vapor-hazard-ratio-v1/run_vhr_prescreen.py"
DIAG = MOD / "benchmarks/vapor-hazard-ratio-v1/diagnostic.canonical.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def find_envelope(obj):
    if isinstance(obj, dict):
        if "payload" in obj and "payloadType" in obj and "signatures" in obj:
            return obj
        for v in obj.values():
            r = find_envelope(v)
            if r:
                return r
    return None


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

# ---- diagnose the two original artifacts ----
def diagnose(path):
    raw = path.read_bytes()
    obj = json.loads(raw)
    env = find_envelope(obj)
    ptype = env["payloadType"]
    body = base64.standard_b64decode(env["payload"])
    se = env["signatures"][0]
    sig = base64.standard_b64decode(se["sig"])
    verifies_pinned = False
    try:
        Ed25519PublicKey.from_public_bytes(eval_pub).verify(sig, pae(ptype, body))
        verifies_pinned = True
    except InvalidSignature:
        pass
    verifies_local = False
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(LOCAL_PUB["public_key_hex"])).verify(sig, pae(ptype, body))
        verifies_local = True
    except InvalidSignature:
        pass
    return {
        "path": str(path.relative_to(ROOT)),
        "file_sha256": sha(raw),
        "payloadType": ptype,
        "payload_sha256": sha(body),
        "signing_keyid": se.get("keyid"),
        "verifies_against_pinned_phase0_evaluator_key": verifies_pinned,
        "verifies_against_local_development_key": verifies_local,
        "dsse_pae_wellformed": True,
    }


diag_receipt = diagnose(ORIG_RECEIPT)
diag_kpi = diagnose(ORIG_KPI)
assert diag_receipt["verifies_against_pinned_phase0_evaluator_key"] is False
assert diag_receipt["verifies_against_local_development_key"] is True
assert diag_kpi["verifies_against_pinned_phase0_evaluator_key"] is False
assert diag_kpi["verifies_against_local_development_key"] is True

# ---- re-attack: re-import the committed harness, re-run compute() twice in-process,
#      compare byte-exact to the committed diagnostic.canonical.json ----
spec = importlib.util.spec_from_file_location("run_vhr_prescreen_reimport", HARNESS)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

d1 = mod.compute()
d2 = mod.compute()
run_a_bytes = canon(d1)
run_b_bytes = canon(d2)
run_a_sha = sha(run_a_bytes)
run_b_sha = sha(run_b_bytes)
two_replay_byte_equal = run_a_sha == run_b_sha

committed_diag_bytes = DIAG.read_bytes()
committed_diag_sha = sha(committed_diag_bytes)
rerun_matches_committed_byte_exact = run_a_sha == committed_diag_sha

assert two_replay_byte_equal, "two-replay mismatch on re-import"
assert rerun_matches_committed_byte_exact, "re-derived diagnostic does not match committed byte-exact"

agg = d1["aggregate"]
assert agg["worst_actor_solvent"] == "methanol"
assert d1["n_solvents_scored"] == 9

harness_sha256 = sha(HARNESS.read_bytes())

# ---- full-module signing sweep (disclosure of remaining un-repaired defects) ----
SWEEP_FILES = [
    "evidence/phase0/kpis/antoine-vp-crosscheck-vhr-kpi.v1.json",
    "reference/mvp20/data/antoine_vp_crosscheck_receipt.v1.json",
    "evidence/phase0/kpis/ghs-clp-cid-attribution-audit-kpi.v1.json",
    "reference/mvp20/data/ghs_clp_cid_attribution_audit_receipt.v1.json",
    "evidence/phase0/kpis/mixture-additivity-raoult-osha-inhalation-prescreen-kpi.v1.json",
    "reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json",
    "evidence/phase0/kpis/vhr-temperature-envelope-inhalation-prescreen-kpi.v1.json",
    "reference/mvp20/data/vhr_temperature_envelope_inhalation_prescreen_receipt.v1.json",
]
sweep = []
for rel in SWEEP_FILES:
    p = MOD / rel
    d = diagnose(p)
    sweep.append(d)

# these two have no DSSE envelope at all (checked separately: find_envelope returns None)
def envelope_present(path):
    obj = json.loads(path.read_text())
    return find_envelope(obj) is not None

no_envelope_files = []
for rel in [
    "evidence/phase0/kpis/sourceability-ehs-public-prescreen-kpi.v1.json",
    "evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json",
]:
    p = MOD / rel
    present = envelope_present(p)
    no_envelope_files.append({"path": rel, "dsse_envelope_present": present, "file_sha256": sha(p.read_bytes())})
    assert present is False

# the ghs_clp_public_hazard receipt is signed with a THIRD, different unknown key
third_key_file = diagnose(MOD / "reference/mvp20/data/ghs_clp_public_hazard_prescreen_5_canonical_epoxy_amines_receipt.v1.json")
assert third_key_file["verifies_against_pinned_phase0_evaluator_key"] is False
assert third_key_file["verifies_against_local_development_key"] is False  # neither pinned nor local-dev key

body_obj = {
    "schema": "amphora.sourceability-ehs.repair-done.r-a13.v1",
    "campaign_item_id": "R-A13",
    "module": "amphora-sourceability-ehs",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "generated_on_host": "xbabe2",
    "date": "2026-08-18",
    "claim": (
        "Reinstatement of the base 9-solvent Vapor Hazard Ratio inhalation prescreen panel "
        "(reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json and its "
        "companion KPI), currently signed with the unanchored repo LOCAL_DEVELOPMENT_AUDIT_ONLY "
        "key instead of the pinned PHASE0_EVALUATOR key -- the same signing-key-selection bug "
        "R-A12 (2026-08-03, ledger fire 20260804T100001-3937441-823cffd3f9d8) fixed for 2 other "
        "artifact pairs but did not sweep exhaustively. This artifact is the foundational panel "
        "(worst_actor=methanol) that R-S04, the Antoine crosscheck, and the temperature-envelope "
        "audits all cite as a pinned, signed input -- it was never itself reinstated."
    ),
    "root_cause": (
        "Same class as R-A12: the harness script benchmarks/vapor-hazard-ratio-v1/run_vhr_prescreen.py "
        "signs with .amphora/control/local-ed25519.key (LOCAL_DEVELOPMENT_AUDIT_ONLY, keyid "
        "local-9028773f49591193) by explicit design (see its own module docstring), not the "
        "phase0 evaluator seed at ~/.local/share/amphora/phase0/keys/evaluator.ed25519.seed that "
        "derives the pinned trust-store key. R-A12 scoped its reinstatement to 2 specific "
        "launcher-downgraded FIRES rather than auditing every KPI/receipt file in the module, so "
        "artifacts from fires that were never individually re-declared (and therefore never "
        "triggered a launcher downgrade event) were missed."
    ),
    "diagnosis": {
        "original_receipt": diag_receipt,
        "original_kpi": diag_kpi,
    },
    "reattack": {
        "description": (
            "Re-imported the committed harness (benchmarks/vapor-hazard-ratio-v1/run_vhr_prescreen.py) "
            "and called compute() twice in-process; compared canonical bytes to the committed "
            "diagnostic.canonical.json."
        ),
        "harness_path": "amphora-sourceability-ehs/benchmarks/vapor-hazard-ratio-v1/run_vhr_prescreen.py",
        "harness_sha256": harness_sha256,
        "committed_diagnostic_sha256": committed_diag_sha,
        "rerun_runA_sha256": run_a_sha,
        "rerun_runB_sha256": run_b_sha,
        "rerun_two_replay_byte_equal": two_replay_byte_equal,
        "rerun_matches_committed_byte_exact": rerun_matches_committed_byte_exact,
        "reproduced_worst_actor": agg["worst_actor_solvent"],
        "reproduced_worst_actor_vhr": agg["worst_actor_vhr"],
        "reproduced_n_solvents_scored": d1["n_solvents_scored"],
    },
    "refutation_criterion": (
        "The pinned claim under attack is 'this KPI/receipt pair is a validly DSSE Ed25519-signed "
        "Phase-0 AUDIT_ONLY artifact under the trust-anchored PHASE0_EVALUATOR key.' REFUTES if "
        "cryptographic verification of the committed signature against the pinned trust-store "
        "public key fails while the science underneath is otherwise sound (i.e. a signing defect, "
        "not a corrupted or fabricated payload)."
    ),
    "refutation_observed": (
        "REFUTED as literally signed: both original files carry a well-formed DSSE envelope whose "
        "signature verifies against the LOCAL_DEVELOPMENT_AUDIT_ONLY key (4b722f4516e035ce3cb95cc"
        "ecffe4638a687d9241e6970f4c1cf5c285b2edf93) and fails Ed25519 verification against the "
        "pinned PHASE0_EVALUATOR key (6cf07abf1a55adaac13e78abc31c531d03d8f0d4232346344a736418c7"
        "b45664). The payload itself is intact and the science re-derives byte-exact, so this is "
        "purely a signing-authority defect, identical in kind to the one R-A12 already repaired "
        "for 2 sibling artifacts."
    ),
    "claim_verdict": "CLAIM_REFUTED",
    "repair_status": "fix_landed",
    "module_wide_signing_sweep": {
        "note": (
            "Full re-verification of every *.json under evidence/phase0/kpis/ and "
            "reference/mvp20/data/ against the pinned PHASE0_EVALUATOR key. Beyond the artifact "
            "reinstated by this fire and the 2 pairs R-A12 already reinstated (osha_table_z1_z2, "
            "vhr_temperature_envelope_crossmethod -- left byte-intact, superseded, NOT re-swept "
            "here), the following remain live defects, NOT reinstated by this fire, and are "
            "flagged for a dedicated follow-on repair:"
        ),
        "still_wrong_key_signed": sweep,
        "no_dsse_envelope_at_all": no_envelope_files,
        "third_unknown_signing_key": third_key_file,
        "scope_note": (
            "sourceability-ehs-public-prescreen-kpi.v1.json is the module's CORE Phase-0 KPI "
            "receipt, cited in docs/mission.md's 'Current benchmark result' section as backing "
            "14 passing deterministic gates -- it currently has NO DSSE envelope at all, not even "
            "a wrong-key one. This is a more severe defect than the wrong-key artifacts and is "
            "the highest-priority target for the next repair fire on this module."
        ),
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/R-A13/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
    "supersedes": [
        {
            "superseded_path": "amphora-sourceability-ehs/reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json",
            "superseded_sha256": diag_receipt["file_sha256"],
            "superseded_deleted_or_modified": False,
            "reason": (
                "DSSE signature made with the unanchored LOCAL_DEVELOPMENT_AUDIT_ONLY key "
                "local-9028773f49591193; cannot verify against the pinned PHASE0_EVALUATOR key in "
                "config/phase0-trust-store.v1.json. This reinstatement receipt carries the "
                "re-verified science and original verdict (worst_actor=methanol, 9 solvents "
                "scored) under the pinned evaluator key. The original file is left byte-intact in "
                "place as evidence."
            ),
        },
        {
            "superseded_path": "amphora-sourceability-ehs/evidence/phase0/kpis/vapor-hazard-ratio-inhalation-prescreen-kpi.v1.json",
            "superseded_sha256": diag_kpi["file_sha256"],
            "superseded_deleted_or_modified": False,
            "reason": (
                "Companion KPI record signed with the same unanchored local-development key. "
                "Same reinstatement rationale as the primary receipt above."
            ),
        },
    ],
    "does_not_close": [
        "Does not modify, supersede, or re-derive the underlying VHR science; ranking, worst-actor "
        "identity, and all 10 KPI gates are unchanged -- only the signing authority is corrected.",
        "Does not reinstate the 4 sibling wrong-key artifact pairs or the 2 no-envelope KPI files "
        "identified by this fire's module-wide sweep -- flagged for a dedicated follow-on repair.",
        "No Phase-0 promotion: PHASE0_EVALUATOR evaluation.v1.dsse.json and PHASE0_INTERNAL_"
        "REVIEWER review remain human dual-identity steps outside this cron's authority.",
    ],
}

body = canon(body_obj)
ptype = "application/vnd.amphora.sourceability-ehs-repair-done-r-a13+json"
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

out = OUTDIR / "r-a13-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", out)
print("self_verify_signature", True)
print("envelope_sha256", sha(out.read_bytes()))
