#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-S04 campaign-item done receipt: certifies the
tightest-margin solvent-pair VHR band-assignment stress test under the
quantified Antoine-vs-CC+Watson(1943) VP method bias (+4.927% to +11.042%,
pulled verbatim from the signed crossmethod-audit receipt's 18 crossmethod
rows), covering the 5 tightest-margin adjacent pairs from the pinned 9-solvent
25C VHR panel, with a positive control showing the harness detects a band
flip planted in its own input. AUDIT_ONLY: does not promote authority, does
not flip scientific_readiness, does not modify the portfolio manifest or any
locked dataset, and does not modify either attacked receipt.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

WORKDIR = MOD / "evidence/phase0/repairs/R-S04/work"
SCRIPT = WORKDIR / "run_tightmargin_bias_propagation.py"
DIAG_A = WORKDIR / "diagnostic.canonical.json"
DIAG_B = WORKDIR / "diagnostic.runB.json"
OUTDIR = MOD / "evidence/phase0/repairs/R-S04/done"


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


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

diag_a_bytes = DIAG_A.read_bytes()
diag_b_bytes = DIAG_B.read_bytes()
diag_a = json.loads(diag_a_bytes)
two_replay_byte_identical = sha(diag_a_bytes) == sha(diag_b_bytes)
assert two_replay_byte_identical, "two-replay byte-stability gate FAILED"

real = diag_a["real"]
pc = diag_a["positive_control"]

assert real["n_panel"] == 9
assert len(real["tightest_5_pairs_evaluated"]) == 5
assert real["any_band_assignment_flip"] is False
assert real["worst_actor_call_flips_under_worstcase_bias"] is False
assert pc["detected"] is True
assert pc["evidence"]["any_band_assignment_flip"] is True

body_obj = {
    "schema": "amphora.sourceability-ehs.repair-done.r-s04.v1",
    "campaign_item_id": "R-S04",
    "module": "amphora-sourceability-ehs",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "claim_under_attack": {
        "receipt_path": "amphora-sourceability-ehs/reference/mvp20/data/vhr_temperature_envelope_crossmethod_audit_receipt.v1.json",
        "claim_text": "The +5-11% systematic VP bias between Antoine and Clausius-Clapeyron+Watson methods does not change any VHR band assignment for a tighter-margin solvent panel.",
        "prior_fire": "20260803T050001 (fire ts 2026-08-03T05:07:35Z) established the +5-11% bias on 3 solvents (toluene, ethylbenzene, MEK) with independent Tb/dHvap anchors and found it did not flip worst-actor invariance or the band-migrator set on the full 6-solvent temperature-envelope panel. This fire is the pre-registered follow-on: construct the TIGHTEST-margin adjacent pairs from the full pinned 9-solvent 25C panel and propagate the bias through both members of each pair as an explicit worst-case stress test, rather than relying on the panel's natural (wide-margin) separations.",
    },
    "method": {
        "panel_source": "amphora-sourceability-ehs/reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json#/kpis/solvent_cards_ranked (pinned, signed, n_solvents_scored=9)",
        "bias_source": "amphora-sourceability-ehs/reference/mvp20/data/vhr_temperature_envelope_crossmethod_audit_receipt.v1.json#/kpis/ccwatson_crossmethod_rows (18 rows, 3 solvents x 6 grid temperatures; bias_min=4.927%, bias_max=11.042%, taken verbatim as observed min/max relative_deviation, not re-derived or re-estimated)",
        "pair_construction": "Rank all 9 panel solvents by 25C VHR descending; form the 8 consecutive-rank ('adjacent-band') pairs; take the 5 with smallest relative separation (VHR_higher/VHR_lower - 1).",
        "stress_test": "For each of the 5 tightest pairs, apply bias_max to the lower-VHR member (pushes it up the most) and bias_min to the higher-VHR member (pushes it up the least) -- the single most-adversarial admissible combination given the bias is uniformly VP-positive-signed in every one of the 18 observed rows. Check for (a) rank-order reversal, (b) screening-band label change for either member.",
        "harness_sha256": sha(SCRIPT.read_bytes()),
        "harness_path": "evidence/phase0/repairs/R-S04/work/run_tightmargin_bias_propagation.py",
        "two_replay_byte_identical": two_replay_byte_identical,
        "diagnostic_canonical_sha256": sha(diag_a_bytes),
        "diagnostic_runB_sha256": sha(diag_b_bytes),
    },
    "refutation_criterion": (
        "Attack REFUTES the pinned claim if, for any of the 5 tightest-margin adjacent pairs "
        "in the 9-solvent panel, applying bias_max to the lower-VHR member and bias_min to the "
        "higher-VHR member causes either member's screening_band label to change, OR if the "
        "same worst-case combination applied to methanol (worst actor) vs mek_2_butanone "
        "(runner-up) reverses the worst-actor call."
    ),
    "tightest_5_pairs": [
        {
            "pair": f"{e['higher_vhr_solvent']}/{e['lower_vhr_solvent']}",
            "relative_separation": round(e["relative_separation"], 4),
            "higher_vhr_solvent": e["higher_vhr_solvent"],
            "higher_vhr_baseline": e["higher_vhr"],
            "higher_band_baseline": e["higher_band"],
            "higher_vhr_worstcase_biased": e["higher_vhr_worstcase_biased"],
            "higher_band_worstcase_biased": e["higher_band_worstcase_biased"],
            "lower_vhr_solvent": e["lower_vhr_solvent"],
            "lower_vhr_baseline": e["lower_vhr"],
            "lower_band_baseline": e["lower_band"],
            "lower_vhr_worstcase_biased": e["lower_vhr_worstcase_biased"],
            "lower_band_worstcase_biased": e["lower_band_worstcase_biased"],
            "band_assignment_flips": e["band_assignment_flips_under_worstcase_bias"],
            "rank_order_flips_within_band": e["rank_order_flips_under_worstcase_bias"],
        }
        for e in real["tightest_5_pairs_evaluated"]
    ],
    "flip_thresholds": {
        "rank_order_flip_first_possible_at_relative_separation": real["rank_order_flip_threshold_relative_separation"],
        "rank_order_flip_threshold_explanation": (
            "Any adjacent pair with relative separation <= 5.828% can have its internal rank "
            "order (not its band label) reversed by the worst-case admissible combination of "
            "the quantified bias. Exactly 1 of the 5 tightest pairs (cyclohexanone/m_xylene, "
            "separation 3.61%) falls under this threshold and its rank order DOES flip under "
            "worst-case bias -- both members remain in the HIGH band before and after, so this "
            "is NOT a band-assignment flip and is outside the scope of the pinned claim, but is "
            "reported here for honesty."
        ),
        "band_assignment_flip_thresholds": real["band_assignment_flip_thresholds"],
        "band_assignment_flip_explanation": (
            "The panel's only HIGH/MODERATE boundary-adjacent solvent is n_butanol (VHR=88.158, "
            "MODERATE). It would need a 13.433% VP bias to cross into HIGH; the quantified "
            "bias envelope's max is 11.042%, 2.391 percentage points (18% relative) short of "
            "the crossing. No other panel solvent is within reach of a band boundary at any "
            "quantified bias magnitude."
        ),
    },
    "verdicts": {
        "any_band_assignment_flip": real["any_band_assignment_flip"],
        "any_rank_order_flip_within_band": real["any_rank_order_flip_within_band"],
        "worst_actor": real["worst_actor"],
        "worst_actor_margin_over_second_place": real["worst_actor_margin_over_second_place"],
        "worst_actor_call_flips_under_worstcase_bias": real["worst_actor_call_flips_under_worstcase_bias"],
    },
    "refutation_observed": (
        "Not observed for the pinned claim (band assignment). Across all 5 tightest-margin "
        "adjacent pairs from the 9-solvent panel, applying the quantified +4.927%/+11.042% "
        "bias envelope in the single most-adversarial admissible combination flips ZERO "
        "screening-band labels; the worst-actor call (methanol, 40.2% margin over "
        "mek_2_butanone) is untouched. The claim as literally stated -- 'does not change any "
        "VHR band assignment' -- SURVIVES. Honest ancillary finding, outside the pinned claim's "
        "scope: internal rank order within the HIGH band is NOT robust for the single tightest "
        "pair (cyclohexanone/m_xylene, 3.61% separation, below the 5.828% rank-flip threshold) "
        "-- their relative order reverses under worst-case bias even though both stay HIGH."
    ),
    "claim_verdict": "CLAIM_SURVIVED",
    "done_criterion": (
        ">=5 tightest-margin solvent pairs enumerated with VHR-band separation, the +5-11% "
        "method bias propagated through both members of each pair, an explicit flips/does-not-"
        "flip verdict per pair plus a verdict on the worst-actor call, and the separation at "
        "which a flip first becomes possible. On CLAIM_SURVIVED, positive_control required."
    ),
    "done_criterion_met": True,
    "positive_control": {
        "planted_defect": pc["planted_defect"],
        "how_planted": pc["how_planted"],
        "detected": pc["detected"],
        "evidence_any_band_assignment_flip": pc["evidence"]["any_band_assignment_flip"],
        "evidence_tightest_5_pairs": [
            {
                "pair": f"{e['higher_vhr_solvent']}/{e['lower_vhr_solvent']}",
                "band_assignment_flips": e["band_assignment_flips_under_worstcase_bias"],
                "lower_band_baseline": e["lower_band"],
                "lower_band_worstcase_biased": e["lower_band_worstcase_biased"],
            }
            for e in pc["evidence"]["tightest_5_pairs_evaluated"]
        ],
    },
    "does_not_close": [
        "Does not modify, supersede, or re-derive either attacked receipt (vhr_temperature_"
        "envelope_crossmethod_audit_receipt.v1.json or vapor_hazard_ratio_inhalation_prescreen_"
        "receipt.v1.json), which remain the authoritative signed KPI records.",
        "No OSHA compliance, control-banding, respirator-selection, procurement-approval, or "
        "regulatory-closure authority. AUDIT_ONLY falsification receipt.",
        "The bias envelope (4.927%-11.042%) is empirically anchored on only 3 of the 9 panel "
        "solvents (toluene, ethylbenzene, MEK) that have independent Tb/dHvap anchors; applying "
        "it uniformly to all 9 as a stress bound is conservative-by-construction, not a claim "
        "that every solvent's true CC+Watson bias falls in this exact range.",
        "No Phase-0 promotion: PHASE0_EVALUATOR evaluation.v1.dsse.json and PHASE0_INTERNAL_"
        "REVIEWER review remain human dual-identity steps outside this cron's authority.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/R-S04/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.sourceability-ehs-repair-done-r-s04+json"
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

OUTDIR.mkdir(parents=True, exist_ok=True)
out = OUTDIR / "r-s04-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", out)
print("self_verify_signature", True)
print("envelope_sha256", sha(out.read_bytes()))
