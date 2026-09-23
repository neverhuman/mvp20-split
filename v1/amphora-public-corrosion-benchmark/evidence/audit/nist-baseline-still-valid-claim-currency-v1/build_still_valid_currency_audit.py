#!/usr/bin/env python3
"""
ROTATION-mode attack, fire 20260818T110001-2670188-9e56cf5611d9.

Claim under attack (the strongest currently-standing claim surface in this
module -- the flagship, currently-LIVE, machine-authoritative KPI that
mission.md quotes directly and that RETRACTION-INDEX.md's own R-A08/R-N03
correction chain deliberately preserved as valid):

  evidence/phase0/repairs/R-N03/done/nist-corr-data-marine-steel-corrosion-baseline-kpi.v3.dsse.json
  #corrected_values.still_valid_from_v1.seawater_uncoated_substrate_baselines

R-N03 (2026-08-03) retracted the Ridge-vs-NULL predictive claim but explicitly
carried this descriptive per-material-group reference-rate block forward under
the field name "still_valid_from_v1" -- an affirmative, timestamped claim that
this specific block remains correct. mission.md echoes it verbatim as
"reproduce exactly from the raw CSV and **remain valid**" and calls the Carbon
steel row "the reference number that anti-corrosion coatings must materially
reduce".

Two LATER, independently-signed audits in this same module's own evidence/audit/
tree already contradict that "still valid" claim for 4 of its 5 material
groups:
  - nist-baseline-descriptive-boundary-provenance-v1 (2026-08-14)
  - nist-baseline-full-distribution-unit-provenance-v1 (2026-08-16, T4 escalation)
Both re-derive the mm/yr values from the same raw CSV's independently-tabulated
mils/yr column via the exact 0.0254 mm/mil conversion and find specific
min/max/p25 fields disagree by 59-86% -- far outside a 20% ambient-rounding
bar the other 21/25 fields comfortably clear.

Prior fires attacked (a) the raw data directly [already done, twice], and
(b) whether the CONSOLIDATED INDEX lists every signed receipt [staleness,
3 recurrences] and (c) whether a receipt's own prose agrees with its own
booleans [eis-reproducibility-self-consistency-v1, 2026-08-17]. This attack is
a fourth, orthogonal axis: does the module's FLAGSHIP KPI's own persistence
claim ("still_valid_from_v1") honor the module's own subsequently-signed
evidence? A KPI can be perfectly indexed, internally self-consistent, and
still be lying about its own currency if later audits refuted it and nothing
ever propagated back.

Method: load the live v3 KPI (confirmed via file inspection to be the current
non-superseded flagship KPI: no v4 exists, R-N03/done is the newest KPI file
on disk by content, and it is the one evidence/phase0/kpis/RETRACTION-INDEX.md
and docs/mission.md currently point to). Extract every leaf numeric field
under corrected_values.still_valid_from_v1.seawater_uncoated_substrate_baselines.
Independently, real-Ed25519-verify and load the two later boundary/full-
distribution audit receipts and extract their own breach findings (field,
group, relative_discrepancy, breaches_20pct_bar). Cross-reference by exact
(group, field, value) match against the KPI's still_valid block -- not
re-deriving anything, purely checking whether the KPI's currency claim is
honest given evidence that ALREADY EXISTS, signed, in this module's own tree.
"""
import base64, glob, hashlib, json, os, sys

REPO_ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MODULE_ROOT = os.path.join(REPO_ROOT, "amphora-public-corrosion-benchmark")
SEED_PATH = "/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed"
AUDIT_ID = "nist-baseline-still-valid-claim-currency-v1"

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_signed(path):
    d = json.load(open(path))
    sig = None
    if isinstance(d, dict):
        if isinstance(d.get("signature"), dict) and "payload" in d["signature"]:
            sig = d["signature"]
        elif "payload" in d and "signatures" in d:
            sig = d
    if sig is None:
        raise ValueError(f"{path}: not a recognized DSSE envelope shape")
    payload_bytes = base64.b64decode(sig["payload"])
    payload = json.loads(payload_bytes)
    return payload, sig, payload_bytes


def real_verify(sig, payload_bytes, path):
    """Independent Ed25519 verification against the sig's own embedded pubkey,
    plus cross-check that pubkey against the pinned Phase-0 evaluator seed."""
    seed = open(SEED_PATH, "rb").read()
    pinned_sk = Ed25519PrivateKey.from_private_bytes(seed)
    pinned_pub_hex = pinned_sk.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()

    sig_list = sig.get("signatures")
    if sig_list:
        entry = sig_list[0]
        raw_sig = base64.b64decode(entry["sig"])
        pt = sig.get("payloadType", "")
    else:
        raise ValueError(f"{path}: no signatures[] in envelope")

    d = json.load(open(path))
    pubhex = d.get("reviewer_public_key_hex") or d.get("evaluator_public_key_hex")
    if pubhex is None:
        raise ValueError(f"{path}: no reviewer_public_key_hex/evaluator_public_key_hex at top level")

    pt_b = pt.encode()
    pae = (b"DSSEv1 " + str(len(pt_b)).encode() + b" " + pt_b + b" "
           + str(len(payload_bytes)).encode() + b" " + payload_bytes)
    pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubhex))
    pubkey.verify(raw_sig, pae)  # raises if invalid
    pinned_match = (pubhex == pinned_pub_hex)
    return {"signature_valid": True, "pubkey_matches_pinned_evaluator": pinned_match,
            "pubkey_hex": pubhex}


def flatten_still_valid(block):
    """block: {group: {field: value, ...}, ...} -> [(group, field, value), ...]
    excluding the 'n' integer-count field, which is not a rate value."""
    out = []
    for group, fields in block.items():
        for field, value in fields.items():
            if field == "n":
                continue
            out.append((group, field, value))
    return out


def build():
    os.chdir(MODULE_ROOT)

    kpi_path = "evidence/phase0/repairs/R-N03/done/nist-corr-data-marine-steel-corrosion-baseline-kpi.v3.dsse.json"
    kpi_payload, kpi_sig, kpi_bytes = load_signed(kpi_path)
    kpi_verify = real_verify(kpi_sig, kpi_bytes, kpi_path)

    # Confirm v3 is current: no v4 exists anywhere in evidence/, and no
    # supersedes.superseded_path in any on-disk receipt names the v3 KPI.
    all_kpi_candidates = sorted(
        p for p in glob.glob("evidence/**/*kpi*.json", recursive=True)
        if p.endswith(".dsse.json") or p.endswith("kpi.v1.json")
    )
    superseded_paths = set()
    for p in glob.glob("evidence/**/*.dsse.json", recursive=True):
        try:
            payload, _, _ = load_signed(p)
        except Exception:
            continue
        sup_field = payload.get("supersedes")
        sup_entries = sup_field if isinstance(sup_field, list) else [sup_field] if sup_field else []
        for entry in sup_entries:
            if isinstance(entry, dict):
                sup = entry.get("superseded_path")
                if sup:
                    superseded_paths.add(os.path.normpath(sup))
    kpi_is_superseded = os.path.normpath(kpi_path) in superseded_paths

    still_valid_block = (
        kpi_payload.get("corrected_values", {})
        .get("still_valid_from_v1", {})
        .get("seawater_uncoated_substrate_baselines", {})
    )
    still_valid_leaves = flatten_still_valid(still_valid_block)

    later_audits = [
        "evidence/audit/nist-baseline-descriptive-boundary-provenance-v1/nist-baseline-descriptive-boundary-provenance-receipt.v1.dsse.json",
        "evidence/audit/nist-baseline-full-distribution-unit-provenance-v1/nist-baseline-full-distribution-unit-provenance-receipt.v1.dsse.json",
    ]

    contradictions = []
    audit_summaries = []
    for ap in later_audits:
        a_payload, a_sig, a_bytes = load_signed(ap)
        a_verify = real_verify(a_sig, a_bytes, ap)
        audit_summaries.append({
            "path": ap,
            "sha256": sha256_file(ap),
            "verdict": a_payload.get("verdict"),
            "signature_valid": a_verify["signature_valid"],
            "pubkey_matches_pinned_evaluator": a_verify["pubkey_matches_pinned_evaluator"],
        })

        breaches = []
        tests = a_payload.get("tests", {})
        for test_name, test_body in tests.items():
            if isinstance(test_body, dict) and "breaches" in test_body:
                breaches.extend(test_body["breaches"])
        per_group = None
        for test_name, test_body in tests.items():
            if isinstance(test_body, dict) and "per_group_field_diffs" in test_body:
                per_group = test_body["per_group_field_diffs"]

        for b in breaches:
            group = b["group"]
            # full-distribution-unit-provenance-v1 uses "field" (e.g. "min_mm_yr");
            # descriptive-boundary-provenance-v1 (the earlier, single-row-trace
            # audit) uses "boundary" (e.g. "min") -- normalize to the KPI's own
            # field-name convention.
            field = b.get("field") or (b["boundary"] + "_mm_yr")
            kpi_value = still_valid_block.get(group, {}).get(field)
            match = any(g == group and f == field for (g, f, v) in still_valid_leaves)
            audited_value = None
            if per_group and group in per_group and field in per_group[group]:
                audited_value = per_group[group][field].get("signed")
            value_agrees = (
                kpi_value is not None and audited_value is not None
                and abs(float(kpi_value) - float(audited_value)) < 1e-12
            )
            contradictions.append({
                "group": group,
                "field": field,
                "still_valid_from_v1_value_in_live_kpi": kpi_value,
                "value_present_in_still_valid_block": match,
                "audited_receipt_own_signed_value": audited_value,
                "kpi_value_matches_the_exact_value_the_audit_examined": value_agrees,
                "relative_discrepancy_found_by_audit": b.get("relative_discrepancy"),
                "contradicting_audit": ap,
                "contradicting_audit_verdict": a_payload.get("verdict"),
            })

    # dedupe (both audits may flag overlapping fields; boundary-provenance-v1
    # traced 2 single-row fields, full-distribution-v1 traced all 25 -- keep
    # the full-distribution finding as primary, note boundary-provenance
    # separately for provenance of independence)
    dedup = {}
    for c in contradictions:
        key = (c["group"], c["field"])
        if key not in dedup or c["contradicting_audit"].find("full-distribution") >= 0:
            dedup[key] = c
    unique_contradictions = sorted(dedup.values(), key=lambda c: (c["group"], c["field"]))

    n_groups_affected = len({c["group"] for c in unique_contradictions})
    n_fields_affected = len(unique_contradictions)
    all_values_confirmed = all(c["kpi_value_matches_the_exact_value_the_audit_examined"] for c in unique_contradictions)

    # Check whether RETRACTION-INDEX.md or mission.md already carries a
    # correction note for this specific defect (so we don't double-claim a
    # gap that's already been closed by a repair we missed).
    retraction_index_text = open("evidence/phase0/kpis/RETRACTION-INDEX.md").read()
    mission_text = open("docs/mission.md").read()
    retraction_mentions_descriptive_defect = (
        "full-distribution-unit-provenance" in retraction_index_text
        or "descriptive-boundary-provenance" in retraction_index_text
    )
    mission_mentions_descriptive_defect = (
        "full-distribution-unit-provenance" in mission_text
        or "descriptive-boundary-provenance" in mission_text
        or "unit-provenance" in mission_text
    )

    verdict = (
        "H0_REFUTED"
        if (unique_contradictions and all_values_confirmed and not kpi_is_superseded)
        else "H0_SURVIVED"
    )

    payload_out = {
        "$schema": "amphora.module-audit-receipt.v1",
        "schema": "amphora.public-corrosion-benchmark.nist-baseline-still-valid-claim-currency.v1",
        "audit_id": AUDIT_ID,
        "module_id": "amphora-public-corrosion-benchmark",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "REAL_ARITHMETIC",
        "axis": "governance",
        "phase": "PRE_PHASE_0",
        "campaign_item_id": "",
        "promotes_authority": False,
        "modifies_manifest": False,
        "modifies_signed_phase0_kpi": False,
        "scientific_success_asserted": False,
        "human_review_performed": False,
        "target_claim": (
            kpi_path +
            "#corrected_values.still_valid_from_v1.seawater_uncoated_substrate_baselines "
            "(the module's flagship, currently-live KPI; R-N03's explicit persistence "
            "claim that this descriptive per-material-group block remains correct after "
            "the Ridge-vs-NULL predictive retraction; verbatim-echoed by docs/mission.md "
            "as 'reproduce exactly from the raw CSV and remain valid')"
        ),
        "hypothesis_H0": (
            "Every (group, field) leaf value under the live v3 KPI's "
            "corrected_values.still_valid_from_v1.seawater_uncoated_substrate_baselines "
            "is consistent with (not contradicted by) every currently-signed "
            "evidence/audit/ receipt in this module dated after the still_valid_from_v1 "
            "claim was made."
        ),
        "verdict": verdict,
        "kpi_under_test": {
            "path": kpi_path,
            "sha256": sha256_file(kpi_path),
            "signature_valid": kpi_verify["signature_valid"],
            "pubkey_matches_pinned_evaluator": kpi_verify["pubkey_matches_pinned_evaluator"],
            "confirmed_current_non_superseded": not kpi_is_superseded,
            "n_kpi_candidate_files_considered": len(all_kpi_candidates),
        },
        "still_valid_block_under_test": {
            group: {field: value for field, value in fields.items()}
            for group, fields in still_valid_block.items()
        },
        "contradicting_audits": audit_summaries,
        "contradictions_found": unique_contradictions,
        "totals": {
            "n_groups_in_still_valid_block": len(still_valid_block),
            "n_groups_affected": n_groups_affected,
            "n_fields_affected": n_fields_affected,
            "all_contradicting_values_confirmed_byte_exact_in_kpi": all_values_confirmed,
        },
        "already_indexed_elsewhere": {
            "retraction_index_md_mentions_this_defect": retraction_mentions_descriptive_defect,
            "mission_md_mentions_this_defect": mission_mentions_descriptive_defect,
        },
        "headline": (
            f"Cross-receipt currency audit (not a re-derivation -- prior fires on "
            f"2026-08-14 and 2026-08-16 already re-derived the raw data twice): the "
            f"currently-LIVE flagship KPI ({kpi_path}) carries a field literally named "
            f"'still_valid_from_v1' over its seawater_uncoated_substrate_baselines "
            f"block. {n_fields_affected} of its leaf values, across {n_groups_affected} "
            f"of its {len(still_valid_block)} material groups (Aluminum min_mm_yr, "
            f"Copper min_mm_yr, Nickel max_mm_yr, Stainless p25_mm_yr), are byte-exact "
            f"matches to values that nist-baseline-full-distribution-unit-provenance-v1 "
            f"(signed 2026-08-16, real-Ed25519-verified here) already found to disagree "
            f"with the same raw CSV's own independently-tabulated mils/yr column by "
            f"59-86% -- H0_REFUTED in that receipt. The 'still_valid_from_v1' KPI has "
            f"never been superseded to reflect this: {'RETRACTION-INDEX.md HAS' if retraction_mentions_descriptive_defect else 'RETRACTION-INDEX.md has NOT'} "
            f"been updated, and {'mission.md HAS' if mission_mentions_descriptive_defect else 'mission.md HAS NOT'} "
            f"been updated -- mission.md still tells a reader the table 'reproduce[s] "
            f"exactly from the raw CSV and remain[s] valid' and calls the Carbon-steel "
            f"row 'the reference number that anti-corrosion coatings must materially "
            f"reduce', with zero acknowledgement that 4 of its 5 material-group rows "
            f"carry at least one already-refuted field. Same staleness failure mode "
            f"that recurred 3x on the consolidated index (2026-08-02, -03, -16) and "
            f"once on receipt self-consistency (2026-08-17), now confirmed on the "
            f"module's single most load-bearing artifact."
        ),
        "methodology": {
            "scope": (
                "loads the live v3 KPI (confirmed current: no supersedes.superseded_path "
                f"anywhere in {len(list(glob.glob('evidence/**/*.dsse.json', recursive=True)))} "
                "on-disk DSSE receipts names it) and the 2 later signed audit receipts "
                "that independently re-derived the same descriptive block from raw data; "
                "does not re-run any derivation itself -- pure cross-receipt provenance "
                "reconciliation of evidence that already exists, signed, in this module."
            ),
            "real_signature_verification": (
                "each of the 3 receipts (KPI + 2 audits) is independently Ed25519-"
                "verified via the DSSEv1 PAE construction against its own embedded "
                "reviewer_public_key_hex, which is then cross-checked byte-for-byte "
                "against the pinned Phase-0 evaluator public key derived fresh from "
                f"{SEED_PATH}."
            ),
            "cross_reference": (
                "for each (group, field) breach reported by the later audits' own "
                "'breaches' list, the exact numeric value the audit examined "
                "(tests.*.per_group_field_diffs[group][field].signed) is compared "
                "byte-exact against the live KPI's still_valid_from_v1 value for the "
                "same (group, field) -- confirming the audit was examining the SAME "
                "number the KPI currently asserts is still valid, not a stale or "
                "different value."
            ),
            "determinism": "pure function of on-disk signed-receipt bytes; no randomness.",
        },
        "recommended_repair": (
            "A future R-prefixed repair item should supersede the v3 KPI's "
            "still_valid_from_v1.seawater_uncoated_substrate_baselines block, dropping "
            "or footnoting the 4 unit-inconsistent fields (Aluminum min_mm_yr, Copper "
            "min_mm_yr, Nickel max_mm_yr, Stainless p25_mm_yr) per the full-distribution "
            "audit's own shadow_from_mils-reconstructed values, log the correction in "
            "RETRACTION-INDEX.md, and update the corresponding docs/mission.md table + "
            "'remain valid' prose in the same fire. This audit intentionally performs no "
            "repair itself (ROTATION mode, no R-/V- campaign item bound to this fire)."
        ),
        "does_not_close": [
            "This receipt derives nothing new from raw data; it is a provenance/"
            "currency reconciliation between already-signed receipts.",
            "It does not modify, supersede, or delete the KPI or either contradicting "
            "audit receipt.",
            "The 21/25 fields the full-distribution audit found unit-consistent "
            "(including all of Carbon and alloy steels, the row mission.md singles out "
            "as 'the reference number') are NOT disputed by this audit.",
            "No manifest, no other module's file, and no signed Phase-0 promotion gate "
            "was touched.",
        ],
        "awaiting": [
            "A repair fire (R-prefixed campaign item) to supersede the v3 KPI's "
            "still_valid_from_v1 block and update RETRACTION-INDEX.md + docs/mission.md "
            "in the same fire.",
        ],
    }
    return payload_out


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()


def dsse_sign(payload_bytes, payload_type, seed):
    sk = Ed25519PrivateKey.from_private_bytes(seed)
    pub = sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    keyid = "phase0-evaluator-" + hashlib.sha256(pub).hexdigest()
    pt = payload_type.encode()
    pae = (b"DSSEv1 " + str(len(pt)).encode() + b" " + pt + b" "
           + str(len(payload_bytes)).encode() + b" " + payload_bytes)
    sig = sk.sign(pae)
    env = {"payload": base64.b64encode(payload_bytes).decode(),
           "payloadType": payload_type,
           "signatures": [{"keyid": keyid, "sig": base64.b64encode(sig).decode()}]}
    return env, keyid, pub.hex()


if __name__ == "__main__":
    d1 = build(); b1 = canon(d1); h1 = hashlib.sha256(b1).hexdigest()
    d2 = build(); b2 = canon(d2); h2 = hashlib.sha256(b2).hexdigest()
    assert b1 == b2, "two-replay byte MISMATCH"
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
    print("verdict:", d1["verdict"])
    print("n_fields_affected:", d1["totals"]["n_fields_affected"],
          "n_groups_affected:", d1["totals"]["n_groups_affected"])

    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        outdir = os.path.join(MODULE_ROOT, "evidence/audit", AUDIT_ID)
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "diagnostic.canonical.json"), "wb") as f:
            f.write(b1)
        with open(os.path.join(outdir, "diagnostic.runB.json"), "wb") as f:
            f.write(b2)
        seed = open(SEED_PATH, "rb").read()
        pt = "application/vnd.amphora.public-corrosion-benchmark-nist-baseline-still-valid-claim-currency.v1+json"
        env, keyid, pubhex = dsse_sign(b1, pt, seed)
        receipt = {"signature": env, "evaluator_key_id": keyid, "reviewer_public_key_hex": pubhex}
        outpath = os.path.join(outdir, "nist-baseline-still-valid-claim-currency-receipt.v1.dsse.json")
        with open(outpath, "w") as f:
            f.write(json.dumps(receipt, indent=2, sort_keys=True))
        print("emitted diagnostic + signed receipt:", outpath)

        raw_sig = base64.b64decode(env["signatures"][0]["sig"])
        payload_bytes = base64.b64decode(env["payload"])
        pt_b = env["payloadType"].encode()
        pae = (b"DSSEv1 " + str(len(pt_b)).encode() + b" " + pt_b + b" "
               + str(len(payload_bytes)).encode() + b" " + payload_bytes)
        pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubhex))
        pubkey.verify(raw_sig, pae)
        print("SELF_VERIFY: PASS keyid", keyid)
