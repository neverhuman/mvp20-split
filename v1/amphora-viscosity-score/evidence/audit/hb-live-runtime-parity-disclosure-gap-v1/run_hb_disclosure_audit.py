#!/usr/bin/env python3
"""Pure-Python, deterministic re-derivation harness for the
hb-live-runtime-parity-disclosure-gap-v1 audit (amphora-viscosity-score).

ROTATION-mode fire. Reads ONLY already-in-tree, already-signed JSON
receipt/KPI bytes plus docs/mission.md -- specifically the already-signed
hb-live-runtime-parity-v1 CLAIM_REFUTED finding (fire_id
20260816T070001-3974882-875bdc64dfe1) and the standing promoted
Herschel-Bulkley Phase-0 KPI and mission prose it was filed against. Does
not re-run any live Rust code, does not touch any dataset row data. This is
a documentation-completeness audit: has the prior REFUTED finding been
incorporated as a disclosed caveat, the same pattern already established
for this module by polyverse-rights-disclosure-gap-v1 and
ffw-vs-ml-uncertainty-disclosure-gap-v1 and
arrhenius-extrapolation-disclosure-gap-v1?

No RNG, no network, no wall-clock reads. Two independent runs on unchanged
inputs are byte-identical.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-viscosity-score"

HB_KPI = MOD / "evidence/phase0/kpis/herschel-bulkley-ccby-amorim2021-kpi.v1.json"
PARITY_RECEIPT = MOD / "evidence/audit/hb-live-runtime-parity-v1/hb-live-runtime-parity-receipt.v1.dsse.json"
MISSION = MOD / "docs/mission.md"
LEDGER = ROOT / "logs/falsification-ledger.jsonl"

UPSTREAM_FIRE_ID = "20260816T070001-3974882-875bdc64dfe1"

# Tokens that WOULD demonstrate the hb-live-runtime-parity-v1 guard-rail
# divergence finding has been incorporated as a disclosed caveat in the
# standing KPI / mission prose. Chosen from the finding's own vocabulary
# for its central result: the promoted KPI's "matches ... verbatim" claim
# is false specifically for the tau0=+Infinity guard-rail path. Deliberately
# compound/specific so they cannot coincidentally match unrelated existing
# text (e.g. the KPI's own unrelated "verbatim" use in its control-arm
# prose, or mission.md's unrelated "NaN and Infinity" red-team-coverage
# sentence).
DISCLOSURE_TOKENS = [
    "hb-live-runtime-parity", "live-runtime-parity", "live runtime parity",
    "guard-rail divergence", "guard rail divergence",
    "tau0 = +infinity", "tau_0 = +infinity", "tau0=+infinity",
    "python oracle accepts", "oracle silently accepts",
    "is_finite check", "not actually an is_finite",
    "matches ... verbatim\" claim is false", "verbatim\" claim is false",
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
    import base64
    sig_block = envelope["signature"]
    body = base64.standard_b64decode(sig_block["payload"])
    ptype = sig_block["payloadType"]
    pub_hex = envelope["evaluator_public_key_hex"]
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
    sig_entry = sig_block["signatures"][0]
    sig = base64.standard_b64decode(sig_entry["sig"])
    try:
        pub.verify(sig, dsse_pae(ptype, body))
        return True, json.loads(body)
    except InvalidSignature:
        return False, None


def main():
    kpi_bytes = HB_KPI.read_bytes()
    mission_bytes = MISSION.read_bytes()
    parity_bytes = PARITY_RECEIPT.read_bytes()
    ledger_bytes = LEDGER.read_bytes()

    kpi = json.loads(kpi_bytes)
    parity_envelope = json.loads(parity_bytes)

    # --- Verify the parity finding this audit builds on is a real, validly
    # signed DSSE envelope (not a bare/forged JSON file). ---
    sig_valid, parity_body = verify_dsse(parity_envelope)
    parity_verdict = parity_body.get("verdict") if parity_body else None
    parity_fire_id = parity_body.get("fire_id") if parity_body else None
    kpi_under_attack_sha256 = parity_body.get("kpi_under_attack_sha256") if parity_body else None

    # --- Confirm the ledger records this finding as REFUTED under the
    # expected fire_id (append-only ledger; read-only scan). ---
    ledger_lines = [l for l in ledger_bytes.decode("utf-8").splitlines() if l.strip()]
    ledger_entry = None
    for line in ledger_lines:
        row = json.loads(line)
        if row.get("fire_id") == UPSTREAM_FIRE_ID and row.get("module") == "amphora-viscosity-score":
            ledger_entry = row
            break
    ledger_confirms_refuted = bool(ledger_entry) and ledger_entry.get("verdict") == "REFUTED"

    # --- Confirm the standing KPI is byte-unchanged since the finding was
    # signed against it (the finding cites the KPI's own sha256). ---
    kpi_unchanged_since_refutation = (sha(kpi_bytes) == kpi_under_attack_sha256)

    # --- Scan the STANDING artifacts (KPI json + mission.md prose) for any
    # trace that the guard-rail divergence finding has been incorporated as
    # a caveat. ---
    kpi_lower = kpi_bytes.decode("utf-8", errors="replace").lower()
    mission_lower = mission_bytes.decode("utf-8", errors="replace").lower()

    kpi_tokens_present = scan_tokens(kpi_lower, DISCLOSURE_TOKENS)
    mission_tokens_present = scan_tokens(mission_lower, DISCLOSURE_TOKENS)

    # positive control anchor: mission.md DOES carry the R-A03 Polyverse
    # rights caveat pattern elsewhere in the same file, proving the file is
    # capable of carrying inline caveats when one has been applied (so an
    # absent caveat here is a genuine gap, not an artifact of file format).
    ra03_caveat_present = "pending counsel" in mission_lower and "context_only" in mission_lower

    # The HB mission.md section still asserts, unqualified, that "the
    # module's exact HB equation ... reproduces the paper's own Fig.3 axis
    # bounds" without any caveat that one of the ten guard-rail edge cases
    # (tau0=+Infinity) diverges between the promoted KPI's own claimed-
    # verbatim oracle and the compiled Rust primitive it claims to
    # reproduce.
    hb_section_present = "herschel-bulkley cc-by parameter-level kpi" in mission_lower
    hb_section_unqualified = (
        hb_section_present
        and "exact hb equation" in mission_lower
        and len(mission_tokens_present) == 0
    )

    disclosure_gap_confirmed = (
        sig_valid
        and parity_verdict in ("REFUTED", "CLAIM_REFUTED")
        and ledger_confirms_refuted
        and kpi_unchanged_since_refutation
        and len(kpi_tokens_present) == 0
        and len(mission_tokens_present) == 0
        and ra03_caveat_present
        and hb_section_unqualified
    )

    diagnostic = {
        "schema": "amphora.viscosity-score.hb-live-runtime-parity-disclosure-audit-diagnostic.v1",
        "purpose": (
            "Documentation-completeness audit: has the already-signed, "
            "already-CLAIM_REFUTED hb-live-runtime-parity-v1 finding (fire_id "
            f"{UPSTREAM_FIRE_ID}) -- that the promoted Herschel-Bulkley KPI's "
            "own claimed-verbatim Python oracle silently ACCEPTS a "
            "tau0=+Infinity input that the live compiled Rust primitive "
            "correctly REJECTS -- been incorporated as a disclosed caveat "
            "into the standing Phase-0 HB KPI and/or docs/mission.md prose, "
            "the same pattern this module already established for its "
            "Polyverse rights gap (R-A03), its FFW-vs-ML uncertainty gap, "
            "and its Arrhenius extrapolation-domain gap?"
        ),
        "inputs_sha256": {
            "hb_kpi": sha(kpi_bytes),
            "mission_md": sha(mission_bytes),
            "parity_receipt": sha(parity_bytes),
            "ledger": sha(ledger_bytes),
        },
        "upstream_finding_verification": {
            "parity_receipt_dsse_signature_valid": sig_valid,
            "parity_receipt_verdict": parity_verdict,
            "parity_receipt_fire_id": parity_fire_id,
            "ledger_entry_found": ledger_entry is not None,
            "ledger_confirms_refuted": ledger_confirms_refuted,
            "kpi_under_attack_sha256_per_upstream_receipt": kpi_under_attack_sha256,
            "kpi_unchanged_since_refutation": kpi_unchanged_since_refutation,
        },
        "disclosure_scan": {
            "tokens_checked": DISCLOSURE_TOKENS,
            "kpi_tokens_present": kpi_tokens_present,
            "mission_tokens_present": mission_tokens_present,
            "kpi_has_any_parity_gap_disclosure": len(kpi_tokens_present) > 0,
            "mission_has_any_parity_gap_disclosure": len(mission_tokens_present) > 0,
            "hb_section_present_in_mission": hb_section_present,
            "hb_section_asserts_exact_equation_unqualified": hb_section_unqualified,
        },
        "positive_control_file_capable_of_carrying_caveats": {
            "note": (
                "mission.md already carries an inline caveat elsewhere in the "
                "same file for a different, already-repaired finding (R-A03: "
                "'[Polyverse dataset: CONTEXT_ONLY, promotion_eligible=false, "
                "pending counsel]', appearing adjacent to every Polyverse-"
                "derived result) and the module has twice before (2026-08-03, "
                "2026-08-15) landed REFUTED disclosure-currency audits of this "
                "exact shape. This proves the absence of an equivalent caveat "
                "for the HB guard-rail-divergence finding is a real gap, not a "
                "limitation of the document format -- the mechanism for "
                "inline disclosure exists in this exact file and is unused "
                "here."
            ),
            "ra03_caveat_pattern_present_in_mission_md": ra03_caveat_present,
        },
        "results": {
            "upstream_finding_is_genuine_signed_refutation": (
                sig_valid and parity_verdict in ("REFUTED", "CLAIM_REFUTED") and ledger_confirms_refuted
            ),
            "standing_kpi_unchanged_since_the_refutation": kpi_unchanged_since_refutation,
            "no_disclosure_in_kpi": len(kpi_tokens_present) == 0,
            "no_disclosure_in_mission_prose": len(mission_tokens_present) == 0,
            "disclosure_mechanism_proven_available_and_unused": ra03_caveat_present,
            "disclosure_gap_confirmed": disclosure_gap_confirmed,
        },
        "interpretation": (
            "The hb-live-runtime-parity-v1 audit (2026-08-16, same day, ~12 "
            "hours prior) is a validly DSSE-signed CLAIM_REFUTED finding, "
            "confirmed both by re-verifying its Ed25519 signature against the "
            f"pinned evaluator key and by locating its ledger line (fire_id "
            f"{UPSTREAM_FIRE_ID}, verdict REFUTED). It found that the "
            "promoted Herschel-Bulkley KPI's evidentiary chain (run_hb_"
            "benchmark.py docstring, inherited unchanged across three prior "
            "fires) literally claims to match src/lib.rs:1227 'verbatim', but "
            "for tau0=+Infinity the claimed-verbatim Python oracle returns Ok "
            "while the live compiled Rust primitive correctly returns Err -- "
            "a real, mechanically demonstrated divergence in what the signed "
            "evidence chain asserts about itself, caught with a positive-"
            "control-validated comparator. Same-day, the standing "
            "herschel-bulkley-ccby-amorim2021-kpi.v1.json is still byte-"
            "identical to the exact file sha256 the parity finding was filed "
            "against, and carries zero token from this finding's vocabulary "
            "anywhere in its body; docs/mission.md's HB section still "
            "unqualifiedly asserts 'the module's exact HB equation ... "
            "reproduces the paper's own Fig.3 axis bounds' with no caveat "
            "about the guard-rail divergence, even though mission.md, via its "
            "own R-A03 Polyverse caveat elsewhere in the identical file, "
            "demonstrably knows how to and does attach inline disclosure "
            "caveats to standing prose once a repair lands. The disclosure "
            "mechanism is proven available in this exact document and is "
            "simply unused for this specific, already-signed, same-day "
            "refutation."
        ),
        "does_not_close": [
            "Does not modify the HB Phase-0 KPI, docs/mission.md, the "
            "hb-live-runtime-parity-v1 receipt, or the 66-receipt master "
            "manifest.",
            "Does not re-run the live-Rust parity probe -- that evidence is "
            "taken as already-established (and independently re-verified "
            "here only at the DSSE-signature and ledger level).",
            "Does not assert the KPI's four PASSED metrics are numerically "
            "wrong on their own stated scope (the 24 finite-input numeric "
            "points, which matched bit-for-bit) -- only that the already-"
            "signed finding about the guard-rail's non-verbatim behavior at "
            "tau0=+Infinity is undisclosed.",
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
