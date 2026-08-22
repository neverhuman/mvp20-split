#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-viscosity-score Arrhenius extrapolation-
finding disclosure-gap audit (ROTATION-mode fire, fire_id
20260815T010001-353480-2f4035e75ae4). AUDIT_ONLY: does NOT promote the
module, does NOT edit the Arrhenius Phase-0 KPI receipt or docs/mission.md,
does NOT modify the 66-receipt master manifest, does NOT re-run the live-Rust
extrapolation probe -- only already-signed downstream JSON KPI/receipt bytes
and the append-only ledger were read."""
import base64, hashlib, json, subprocess
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"
EV = MOD / "evidence/audit/arrhenius-extrapolation-disclosure-gap-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260815T010001-353480-2f4035e75ae4"


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


canon = (EV / "diagnostic.canonical.json").read_bytes()
runB = (EV / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["verdict"] == "REFUTED", f"unexpected verdict {diag['verdict']}"
assert diag["results"]["disclosure_gap_confirmed"] is True

# independent 3rd confirmatory replay into a temp path
third = EV / "diagnostic.runC.tmp.json"
subprocess.run(["python3", str(EV / "run_arrhenius_disclosure_audit.py"), str(third)],
               check=True, cwd=str(EV))
third_sha = sha(third.read_bytes())
third.unlink()
assert third_sha == diag_sha, f"3rd replay FAIL {third_sha} != {diag_sha}"

harness_sha = sha((EV / "run_arrhenius_disclosure_audit.py").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text()) if TRUST.exists() else {"keys": []}
tbr = {k.get("role"): k for k in trust.get("keys", [])}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

body_obj = {
    "schema": "amphora.viscosity-score.arrhenius-extrapolation-disclosure-gap-receipt.v1",
    "receipt_id": "arrhenius-extrapolation-disclosure-gap-v1",
    "module_id": "amphora-viscosity-score",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "mode": "ROTATION",
    "fire_id": FIRE_ID,
    "date": "2026-08-15",
    "scientific_success_required_for_phase0": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_mission_md": False,
    "modifies_signed_phase0_kpi": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "derives_from_quarantined_row_data": False,
    "claim_under_attack": (
        "docs/mission.md standing prose and evidence/phase0/kpis/"
        "viscosity-arrhenius-kpi.v1.json (sha256 "
        "fcfa296871935e0f33a023ad6d7a4c1f69dc982e31dc341bfcfa749b3655ec93) "
        "-- read one fire-day after the module's own signed, ledgered "
        "arrhenius-extrapolation-domain-gap-v1 REFUTED finding (fire_id "
        "20260814T130001-2255528-544555cc0ef7) -- amount to a standing claim "
        "that the module's Phase-0 Arrhenius disclosure is complete and "
        "up to date with its own attack history."
    ),
    "attack": (
        "Documentation-completeness / disclosure-currency audit, the same "
        "pattern already established in this module by "
        "polyverse-rights-disclosure-gap-v1 and "
        "ffw-vs-ml-uncertainty-disclosure-gap-v1. Independently re-verified "
        "the Ed25519 DSSE signature of the prior day's "
        "arrhenius-extrapolation-domain-gap-v1 receipt against the pinned "
        "evaluator public key (not merely trusting the file), and confirmed "
        "its ledger line (fire_id 20260814T130001-2255528-544555cc0ef7, "
        "verdict REFUTED) is present in the append-only "
        "logs/falsification-ledger.jsonl. That finding established: (1) "
        "`held_out_temperature_extrapolation_mape` is mislabeled -- its 30C "
        "probe point is interpolation, strictly inside the fitted [20,60]C "
        "span; (2) the module's only temperature guard "
        "(finite_between(-273.14, 500.0)) is a physical-plausibility bound "
        "that accepted 12/12 genuinely out-of-fitted-window probe calls with "
        "zero rejections; (3) glycerol, evaluated at genuinely out-of-window "
        "temperatures against an independent published table, breaches the "
        "module's own +/-10% per-solvent quality floor by up to 42.8% (a "
        "silent Ok(_), not an error). This audit then scanned the STANDING "
        "KPI json and mission.md prose (unchanged since that refutation, per "
        "sha256) for any of that finding's vocabulary (out-of-window, fitted/"
        "fitting window, mislabel, glass-forming, Vogel-Fulcher, "
        "domain-of-validity, the 42.8% figure itself) and found zero tokens "
        "in either file. As a positive control proving the absence is a real "
        "gap and not a limitation of the document format, this audit also "
        "confirmed mission.md DOES already carry an equivalent inline "
        "caveat elsewhere in the identical file for a different, "
        "already-repaired finding (the R-A03 Polyverse "
        "'[...CONTEXT_ONLY, promotion_eligible=false, pending counsel]' "
        "caveat) -- so the module both knows how to and does attach this "
        "class of disclosure when a repair item lands it, and simply has not "
        "yet done so for the Arrhenius domain-gap finding."
    ),
    "refutation_criterion": (
        "The claim SURVIVES if either the Arrhenius KPI json or docs/"
        "mission.md prose already discloses, in any form, the "
        "arrhenius-extrapolation-domain-gap-v1 finding's substance (that the "
        "range guard is not a domain-of-validity check, that "
        "held_out_temperature_extrapolation_mape is actually interpolation, "
        "or the concrete glycerol out-of-window failure magnitude) -- OR if "
        "the upstream finding it rests on turns out not to be a genuinely "
        "signed, ledgered REFUTED verdict. It is REFUTED if: (1) the upstream "
        "domain-gap receipt's DSSE signature independently re-verifies "
        "against the pinned evaluator key and its ledger line confirms "
        "verdict REFUTED; (2) the standing KPI json still cites both attacked "
        "gate names unchanged; (3) neither the KPI json nor mission.md "
        "contains any token from the finding's own vocabulary; and (4) "
        "mission.md is shown, via its own R-A03 caveat elsewhere in the same "
        "file, to be a document where this module already exercises the "
        "inline-disclosure mechanism when a repair has landed it."
    ),
    "verdict": diag["verdict"],
    "results": diag["results"],
    "headline_result": {
        "upstream_finding_is_genuine_signed_refutation": diag["results"]["upstream_finding_is_genuine_signed_refutation"],
        "standing_kpi_unchanged_since_the_refutation": diag["results"]["standing_kpi_unchanged_since_the_refutation"],
        "no_disclosure_in_kpi": diag["results"]["no_disclosure_in_kpi"],
        "no_disclosure_in_mission_prose": diag["results"]["no_disclosure_in_mission_prose"],
        "disclosure_mechanism_proven_available_and_unused": diag["results"]["disclosure_mechanism_proven_available_and_unused"],
        "interpretation": diag["interpretation"],
    },
    "upstream_finding_verification": diag["upstream_finding_verification"],
    "disclosure_scan": diag["disclosure_scan"],
    "positive_control_file_capable_of_carrying_caveats": diag["positive_control_file_capable_of_carrying_caveats"],
    "theory": [
        "Precedent within this module: evidence/audit/"
        "polyverse-rights-disclosure-gap-v1/ and evidence/audit/"
        "ffw-vs-ml-uncertainty-disclosure-gap-v1/, both REFUTED "
        "disclosure-currency audits later repaired under item R-A03.",
        "The upstream physical finding under this audit (glycerol "
        "super-Arrhenius / Vogel-Fulcher-Tammann behavior outside a narrow "
        "fitted window) is established in evidence/audit/"
        "arrhenius-extrapolation-domain-gap-v1/, citing Segur & Oberstar "
        "1951 (Ind. Eng. Chem. 43(9):2117-2120) via Glycerine Producers' "
        "Association 1963.",
    ],
    "does_not_close": diag["does_not_close"],
    "human_action_needed": (
        "File a repair item (analogous to R-A03) to add an inline caveat to "
        "docs/mission.md's Arrhenius KPI section and/or the "
        "viscosity-arrhenius-kpi.v1.json body itself, disclosing: (a) that "
        "held_out_temperature_extrapolation_mape is measured at a point "
        "INSIDE the fitted window (interpolation, not extrapolation), and "
        "(b) that the module's temperature range guard is a physical-"
        "plausibility bound only, not a fitted-domain-of-validity check, so "
        "genuinely out-of-window calls (e.g. glycerol beyond ~60C) can return "
        "silently wrong results up to 42.8% error with no error return. This "
        "is a documentation/methodology completeness action; it does not "
        "require new data or re-running the live-Rust probe, which is "
        "already signed and ledgered."
    ),
    "provenance": {
        "harness_sha256": {"run_arrhenius_disclosure_audit.py": harness_sha},
        "inputs_sha256": diag["inputs_sha256"],
    },
    "reproducibility": {
        "byte_identical": True,
        "two_replay_sha256_gate": "PASS",
        "third_confirmatory_replay": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "third_replay_sha256": third_sha,
        "determinism": (
            "pure-python re-derivation from already-in-tree, already-hashed "
            "JSON/JSONL files; no RNG, no network, no wall-clock reads at run "
            "time."
        ),
    },
    "signing_key": {
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "role": "PHASE0_EVALUATOR",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": eval_pin,
        "used_for": "AUDIT_ONLY arrhenius-extrapolation-disclosure-gap receipt under evidence/audit/",
    },
    "reviewer_reference": {
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "role": "PHASE0_INTERNAL_REVIEWER",
        "derives_pinned_trust_store_key_id": rev_pin,
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.viscosity-score-arrhenius-extrapolation-disclosure-gap+json"
sig = eval_sk.sign(pae(ptype, body))
sig_b64 = base64.standard_b64encode(sig).decode()
envelope = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": {
        "payload": base64.standard_b64encode(body).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": eval_key_id, "sig": sig_b64}],
    },
}
out = EV / "arrhenius-extrapolation-disclosure-gap-receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
