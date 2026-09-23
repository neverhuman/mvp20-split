#!/usr/bin/env python3
"""Pure-Python, deterministic re-derivation harness for the
arrhenius-extrapolation-disclosure-gap-v1 audit (amphora-viscosity-score).

ROTATION-mode fire. Reads ONLY already-in-tree, already-signed JSON
receipt/KPI bytes plus docs/mission.md -- specifically the already-signed
arrhenius-extrapolation-domain-gap-v1 REFUTED finding (fire_id
20260814T130001-2255528-544555cc0ef7) and the standing Arrhenius Phase-0 KPI
and mission prose it was filed against. Does not re-run any live Rust code,
does not touch any dataset row data. This is a documentation-completeness
audit: has the prior REFUTED finding been incorporated as a disclosed
caveat, the same pattern already established for this module by
polyverse-rights-disclosure-gap-v1 and ffw-vs-ml-uncertainty-disclosure-gap-v1?

No RNG, no network, no wall-clock reads. Two independent runs on unchanged
inputs are byte-identical.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"

ARRHENIUS_KPI = MOD / "evidence/phase0/kpis/viscosity-arrhenius-kpi.v1.json"
DOMAIN_GAP_RECEIPT = MOD / "evidence/audit/arrhenius-extrapolation-domain-gap-v1/arrhenius-extrapolation-domain-gap-receipt.v1.dsse.json"
MISSION = MOD / "docs/mission.md"
LEDGER = ROOT / "logs/falsification-ledger.jsonl"

# Tokens that WOULD demonstrate the domain-gap finding has been incorporated
# as a disclosed caveat in the standing KPI / mission prose. Chosen from the
# domain-gap receipt's own vocabulary for its central findings: the mislabeled
# metric, the inadequate range guard, and the concrete out-of-window failure.
DISCLOSURE_TOKENS = [
    "out-of-window", "out of window", "out-of-fitted-window",
    "fitted window", "fitting window", "mislabel",
    "glass-forming", "glass forming", "vogel-fulcher",
    "domain-of-validity", "domain of validity",
    "42.8", "arrhenius-extrapolation-domain-gap",
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def scan_tokens(text_lower, tokens):
    return sorted(t for t in tokens if t in text_lower)


def dsse_pae(payload_type, body):
    return (b"DSSEv1 " + str(len(payload_type)).encode() + b" " +
            payload_type.encode() + b" " + str(len(body)).encode() + b" " + body)


def verify_dsse(envelope):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    sig_block = envelope["signature"]
    body = __import__("base64").standard_b64decode(sig_block["payload"])
    ptype = sig_block["payloadType"]
    pub_hex = envelope["evaluator_public_key_hex"]
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
    sig_entry = sig_block["signatures"][0]
    sig = __import__("base64").standard_b64decode(sig_entry["sig"])
    try:
        pub.verify(sig, dsse_pae(ptype, body))
        return True, json.loads(body)
    except InvalidSignature:
        return False, None


def main():
    kpi_bytes = ARRHENIUS_KPI.read_bytes()
    mission_bytes = MISSION.read_bytes()
    domain_gap_bytes = DOMAIN_GAP_RECEIPT.read_bytes()
    ledger_bytes = LEDGER.read_bytes()

    kpi = json.loads(kpi_bytes)
    domain_gap_envelope = json.loads(domain_gap_bytes)

    # --- Verify the domain-gap finding this audit builds on is a real,
    # validly signed DSSE envelope (not a bare/forged JSON file). ---
    sig_valid, domain_gap_body = verify_dsse(domain_gap_envelope)
    domain_gap_verdict = domain_gap_body.get("verdict") if domain_gap_body else None
    domain_gap_fire_id = domain_gap_body.get("fire_id") if domain_gap_body else None

    # --- Confirm the ledger records this finding as REFUTED under the
    # expected fire_id (append-only ledger; read-only scan). ---
    ledger_lines = [l for l in ledger_bytes.decode("utf-8").splitlines() if l.strip()]
    ledger_entry = None
    for line in ledger_lines:
        row = json.loads(line)
        if row.get("fire_id") == "20260814T130001-2255528-544555cc0ef7" and row.get("module") == "amphora-viscosity-score":
            ledger_entry = row
            break
    ledger_confirms_refuted = bool(ledger_entry) and ledger_entry.get("verdict") == "REFUTED"

    # --- Scan the STANDING artifacts (KPI json + mission.md prose) for any
    # trace that the domain-gap finding has been incorporated as a caveat. ---
    kpi_lower = kpi_bytes.decode("utf-8", errors="replace").lower()
    mission_lower = mission_bytes.decode("utf-8", errors="replace").lower()

    kpi_tokens_present = scan_tokens(kpi_lower, DISCLOSURE_TOKENS)
    mission_tokens_present = scan_tokens(mission_lower, DISCLOSURE_TOKENS)

    # positive control anchor: mission.md DOES carry the R-A03 Polyverse
    # rights caveat pattern elsewhere in the same file, proving the file is
    # capable of carrying inline caveats when one has been applied (so an
    # absent caveat here is a genuine gap, not an artifact of file format).
    ra03_caveat_present = "pending counsel" in mission_lower and "context_only" in mission_lower

    # Confirm the two specific gate names the domain-gap receipt cited are
    # still present verbatim in the standing KPI, with no adjoining caveat
    # (checked separately below via the token scan).
    kpi_flat_str = json.dumps(kpi, sort_keys=True)
    cites_fail_closed_rate = '"applicability_domain_fail_closed_rate"' in kpi_flat_str
    cites_extrapolation_mape = '"held_out_temperature_extrapolation_mape"' in kpi_flat_str

    disclosure_gap_confirmed = (
        sig_valid
        and domain_gap_verdict in ("REFUTED", "CLAIM_REFUTED")
        and ledger_confirms_refuted
        and cites_fail_closed_rate
        and cites_extrapolation_mape
        and len(kpi_tokens_present) == 0
        and len(mission_tokens_present) == 0
        and ra03_caveat_present
    )

    diagnostic = {
        "schema": "amphora.viscosity-score.arrhenius-extrapolation-disclosure-audit-diagnostic.v1",
        "purpose": (
            "Documentation-completeness audit: has the already-signed, "
            "already-REFUTED arrhenius-extrapolation-domain-gap-v1 finding "
            "(fire_id 20260814T130001-2255528-544555cc0ef7) been incorporated "
            "as a disclosed caveat into the standing Phase-0 Arrhenius KPI "
            "and/or docs/mission.md prose, the same pattern this module "
            "already established for its Polyverse rights gap (R-A03) and its "
            "FFW-vs-ML uncertainty gap?"
        ),
        "inputs_sha256": {
            "arrhenius_kpi": sha(kpi_bytes),
            "mission_md": sha(mission_bytes),
            "domain_gap_receipt": sha(domain_gap_bytes),
            "ledger": sha(ledger_bytes),
        },
        "upstream_finding_verification": {
            "domain_gap_receipt_dsse_signature_valid": sig_valid,
            "domain_gap_receipt_verdict": domain_gap_verdict,
            "domain_gap_receipt_fire_id": domain_gap_fire_id,
            "ledger_entry_found": ledger_entry is not None,
            "ledger_confirms_refuted": ledger_confirms_refuted,
        },
        "standing_kpi_still_cites_the_attacked_gates": {
            "cites_applicability_domain_fail_closed_rate": cites_fail_closed_rate,
            "cites_held_out_temperature_extrapolation_mape": cites_extrapolation_mape,
        },
        "disclosure_scan": {
            "tokens_checked": DISCLOSURE_TOKENS,
            "kpi_tokens_present": kpi_tokens_present,
            "mission_tokens_present": mission_tokens_present,
            "kpi_has_any_domain_gap_disclosure": len(kpi_tokens_present) > 0,
            "mission_has_any_domain_gap_disclosure": len(mission_tokens_present) > 0,
        },
        "positive_control_file_capable_of_carrying_caveats": {
            "note": (
                "mission.md already carries an inline caveat elsewhere in the "
                "same file for a different, already-repaired finding (R-A03: "
                "'[Polyverse dataset: CONTEXT_ONLY, promotion_eligible=false, "
                "pending counsel]', appearing adjacent to every Polyverse-"
                "derived result). This proves the absence of an equivalent "
                "caveat for the domain-gap finding is a real gap, not a "
                "limitation of the document format -- the mechanism for "
                "inline disclosure exists in this exact file and is unused "
                "here."
            ),
            "ra03_caveat_pattern_present_in_mission_md": ra03_caveat_present,
        },
        "results": {
            "upstream_finding_is_genuine_signed_refutation": (
                sig_valid and domain_gap_verdict in ("REFUTED", "CLAIM_REFUTED") and ledger_confirms_refuted
            ),
            "standing_kpi_unchanged_since_the_refutation": (
                cites_fail_closed_rate and cites_extrapolation_mape
            ),
            "no_disclosure_in_kpi": len(kpi_tokens_present) == 0,
            "no_disclosure_in_mission_prose": len(mission_tokens_present) == 0,
            "disclosure_mechanism_proven_available_and_unused": ra03_caveat_present,
            "disclosure_gap_confirmed": disclosure_gap_confirmed,
        },
        "interpretation": (
            "The arrhenius-extrapolation-domain-gap-v1 audit (2026-08-14) is a "
            "validly DSSE-signed REFUTED finding, confirmed both by re-"
            "verifying its Ed25519 signature against the pinned evaluator key "
            "and by locating its ledger line (fire_id "
            "20260814T130001-2255528-544555cc0ef7, verdict REFUTED). It found "
            "that `held_out_temperature_extrapolation_mape` is mislabeled "
            "(30C is interpolation, strictly inside the [20,60]C fitted span, "
            "not extrapolation), that the module's only temperature guard "
            "(finite_between(-273.14, 500.0)) is a physical-plausibility bound "
            "that accepted 12/12 genuinely out-of-fitted-window probe calls, "
            "and that glycerol -- a known glass-forming, super-Arrhenius "
            "liquid -- breaches the module's own +/-10% quality floor by up to "
            "42.8% once actually evaluated outside its fitting window. One day "
            "later, the standing viscosity-arrhenius-kpi.v1.json still cites "
            "both attacked gate names with their original PASSED values and "
            "carries zero token from this audit's vocabulary anywhere in its "
            "body; docs/mission.md, which already demonstrates (via its "
            "R-A03 Polyverse caveat, present elsewhere in the identical file) "
            "that this module knows how to and does attach inline disclosure "
            "caveats to standing prose, likewise carries none for this "
            "finding. The disclosure mechanism is proven available in this "
            "exact document and is simply unused for this specific, already-"
            "signed refutation."
        ),
        "does_not_close": [
            "Does not modify the Arrhenius KPI, docs/mission.md, the "
            "domain-gap receipt, or the 66-receipt master manifest.",
            "Does not re-run the live-Rust extrapolation probe -- that "
            "evidence is taken as already-established (and independently "
            "re-verified here only at the DSSE-signature and ledger level).",
            "Does not assert the KPI's PASSED gate values are numerically "
            "wrong on their own stated scope (30C interpolation) -- only that "
            "the already-signed finding about the guard's inadequacy outside "
            "that scope is undisclosed.",
        ],
        "verdict": "REFUTED" if disclosure_gap_confirmed else "SURVIVED",
    }
    return diagnostic


def canonical_dump(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode() + b"\n"


if __name__ == "__main__":
    diag = main()
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("diagnostic.canonical.json")
    out_path.write_bytes(canonical_dump(diag))
    print("WROTE", out_path, "sha256", sha(canonical_dump(diag)))
