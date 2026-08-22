#!/usr/bin/env python3
"""AUDIT_ONLY: registry_manifest_hash pin-freshness audit for
amphora-ip-fto-guard/ip/claim-contract.v1.json and
amphora-ip-fto-guard/evidence/phase0/bundle.v1.json.

Claim under attack: both files pin registry_manifest_hash to
25b7b7f03c46200dae9d1d1da82c67b8dc353070c3cb3690adc7bab52b5753a5, which is
NOT byte-equal to the live root module-manifest.json
(571813eedebd18c71d8f56b1fe454c339cecf10286403b9c5dd1e1599822ff3f, one
registry succession ahead). This module never audited that field before.
On its face this looks like the same class of defect PIN-01/PIN-02 already
found twice in this module (docs/mission.md, capability-profile.json, and
the KPI receipt all carried stale hash pins that had drifted from the live
file). This audit checks whether it is ALSO a real defect here, or whether
it is a legitimate historical pin under amphora-phase0-reviewer's own
registry-succession design (a module's pin only needs to advance when a
registry succession actually edits THAT module's manifest entry).

Refutation criterion (this is what WOULD prove the claim FALSE, i.e. WOULD
show the pin is genuinely stale and not merely historical-but-valid):
  (a) the amphora-ip-fto-guard module-manifest.json entry (canonicalized)
      differs between the pinned snapshot (25b7b7f0...) and the live HEAD
      (571813ee...), meaning some edit to the module's own manifest row
      happened after the pin and was never reflected in the pin; OR
  (b) any registry succession record on the path from the pinned snapshot
      to HEAD lists "amphora-ip-fto-guard" in its `edits`, meaning the
      canonical registry succession mechanism itself says this module WAS
      touched after the pinned snapshot.
If neither (a) nor (b) holds, the pin -- though not byte-equal to the live
manifest file -- still faithfully identifies the CURRENT amphora-ip-fto-guard
manifest entry, and the claim SURVIVES.

Also independently re-derives amphora-phase0-reviewer's own succession-chain
constants (GENESIS/FIRST_HEAD/FIRST_RECORD/SECOND_RECORD, hardcoded in
verify_registry_succession_chain, amphora-phase0-reviewer/src/main.rs) from
the live registry/succession-chain.v1.json + registry/archive/ + module-manifest.json
on disk, and re-implements resolve_registry_manifest()'s "known hash" test,
to confirm the pin is chain-resolvable and not simply un-forked-by-luck.

AUDIT_ONLY. No fetch, no manifest edit, no fixture edit, no registry edit.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-ip-fto-guard"
MODULE_ID = "amphora-ip-fto-guard"

CLAIM_CONTRACT = MODULE / "ip/claim-contract.v1.json"
BUNDLE = MODULE / "evidence/phase0/bundle.v1.json"
LIVE_MANIFEST = ROOT / "module-manifest.json"
CHAIN_FILE = ROOT / "registry/succession-chain.v1.json"
ARCHIVE_DIR = ROOT / "registry/archive"
SUCCESSION_DIR = ROOT / "registry/succession"

# Hardcoded in amphora-phase0-reviewer/src/main.rs::verify_registry_succession_chain
RUST_GENESIS = "be6d3e8023c17a779d8503f3bfcfb15b0020d5ec5c768c9791013ff4134ed6b7"
RUST_FIRST_HEAD = "bff63ed55151f6f9055312a3cd4026fc11edc320c0df61f3593be54d833c87fc"
RUST_FIRST_RECORD = "0be2e86905ad249bfd908889e297ff4871221e4c71ed4cc4d313690738c9fe44"
RUST_SECOND_RECORD = "4331b19bc615f9c559da753dc5a0d23a269f0b033f129350db8ba48e495f099a"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon_entry_sha(manifest_obj, module_id=MODULE_ID):
    mods = [m for m in manifest_obj["modules"] if m.get("project") == module_id]
    assert len(mods) == 1, f"expected exactly 1 manifest entry for {module_id}, got {len(mods)}"
    return sha(json.dumps(mods[0], sort_keys=True).encode()), mods[0]


def load_chain():
    return json.loads(CHAIN_FILE.read_bytes())


def load_succession_records():
    recs = {}
    for f in sorted(SUCCESSION_DIR.glob("*.json")):
        recs[f.stem] = json.loads(f.read_bytes())
    return recs


def resolve_registry_manifest_known(chain, requested_hash):
    """Re-implementation of amphora-phase0-reviewer's resolve_registry_manifest
    'known' predicate: requested_hash must equal genesis or some record's
    successor_sha256."""
    if requested_hash == chain["genesis_manifest_sha256"]:
        return True
    return any(r["successor_sha256"] == requested_hash for r in chain["records"])


def archive_path_for(h):
    return ARCHIVE_DIR / h / "module-manifest.json"


def edits_touching_module_between(chain, records_by_hash, from_hash, to_hash, module_id=MODULE_ID):
    """Walk the ordered succession records strictly after from_hash (exclusive)
    up to and including to_hash, and report every record whose edits list
    names module_id. This mirrors what verify_module_registry_succession's
    registry_succession_for_module() checks, but generalized to a hash range
    instead of a single successor_sha256."""
    ordered = chain["records"]
    touching = []
    seen_from = (from_hash == chain["genesis_manifest_sha256"])
    for rec in ordered:
        if rec["predecessor_sha256"] == from_hash:
            seen_from = True
        if not seen_from:
            continue
        full = records_by_hash.get(rec["record_sha256"])
        edit_modules = [e.get("module_id") for e in (full.get("edits", []) if full else [])]
        if module_id in edit_modules:
            touching.append({"succession_id": rec["succession_id"], "record_sha256": rec["record_sha256"]})
        if rec["successor_sha256"] == to_hash:
            break
    return touching


def main(mutate_manifest_entry=False, forge_succession_edit=False):
    chain = load_chain()
    records_by_hash = load_succession_records()

    live_manifest_bytes = LIVE_MANIFEST.read_bytes()
    live_manifest_sha256 = sha(live_manifest_bytes)
    live_manifest_obj = json.loads(live_manifest_bytes)

    # --- pull the asserted pins straight from the two on-disk files ---
    cc_obj = json.loads(CLAIM_CONTRACT.read_bytes())
    bundle_obj = json.loads(BUNDLE.read_bytes())
    pinned_hash = cc_obj["registry_manifest_hash"]
    bundle_pinned_hash = bundle_obj["registry_manifest_hash"]

    pins_self_consistent = pinned_hash == bundle_pinned_hash

    # --- re-derive amphora-phase0-reviewer's hardcoded chain constants ---
    chain_constants_match_rust = (
        chain["genesis_manifest_sha256"] == RUST_GENESIS
        and chain["records"][0]["successor_sha256"] == RUST_FIRST_HEAD
        and chain["records"][0]["record_sha256"] == RUST_FIRST_RECORD
        and chain["records"][1]["record_sha256"] == RUST_SECOND_RECORD
        and chain["head_manifest_sha256"] == live_manifest_sha256
        and len(chain["records"]) == 3
        and chain["records"][2]["successor_sha256"] == chain["head_manifest_sha256"]
    )

    # --- chain resolvability of the ACTUAL pinned hash ---
    pin_known_to_chain = resolve_registry_manifest_known(chain, pinned_hash)
    pin_archive_path = archive_path_for(pinned_hash)
    pin_archive_bytes = pin_archive_path.read_bytes() if pin_archive_path.exists() else b""
    pin_archive_hash_matches_dirname = sha(pin_archive_bytes) == pinned_hash if pin_archive_bytes else False

    # --- entry-level drift check (part a of refutation criterion) ---
    pinned_manifest_obj = json.loads(pin_archive_bytes) if pin_archive_bytes else None
    pinned_entry_sha, pinned_entry = (
        canon_entry_sha(pinned_manifest_obj) if pinned_manifest_obj else (None, None)
    )
    live_entry_sha, live_entry = canon_entry_sha(live_manifest_obj)

    if mutate_manifest_entry:
        # POSITIVE CONTROL: simulate a real, undisclosed edit to this
        # module's own manifest row after the pin, by mutating a copy of
        # the live manifest object in memory (never touches disk).
        mutated_obj = json.loads(json.dumps(live_manifest_obj))
        for m in mutated_obj["modules"]:
            if m.get("project") == MODULE_ID:
                m["operational_readiness"] = "READY"
                m["readiness"] = "READY"
        live_entry_sha, live_entry = canon_entry_sha(mutated_obj)

    entries_identical = (pinned_entry_sha == live_entry_sha)

    # --- succession-edit check (part b of refutation criterion) ---
    touching_records = edits_touching_module_between(
        chain, records_by_hash, from_hash=pinned_hash, to_hash=chain["head_manifest_sha256"]
    )

    if forge_succession_edit:
        # POSITIVE CONTROL: forge a synthetic 4th succession record that
        # claims to edit amphora-ip-fto-guard between the pin and HEAD, and
        # confirm the walker detects it. Constructed in memory only.
        forged_chain = json.loads(json.dumps(chain))
        forged_records_by_hash = dict(records_by_hash)
        forged_record_sha = "f" * 64  # synthetic, not a real file
        forged_records_by_hash[forged_record_sha] = {
            "edits": [{"module_id": MODULE_ID, "field": "readiness", "new_value": "READY"}]
        }
        forged_chain["records"] = list(chain["records"]) + [{
            "predecessor_sha256": chain["head_manifest_sha256"],
            "record_sha256": forged_record_sha,
            "succession_id": "registry-succession-FORGED-positive-control",
            "successor_sha256": "9" * 64,
        }]
        touching_records = edits_touching_module_between(
            forged_chain, forged_records_by_hash, from_hash=pinned_hash, to_hash="9" * 64
        )

    no_succession_edit_since_pin = len(touching_records) == 0

    # --- overall verdict ---
    part_a_refuted = not entries_identical
    part_b_refuted = not no_succession_edit_since_pin
    h0_refuted = part_a_refuted or part_b_refuted
    h0_verdict = "REFUTED" if h0_refuted else "SURVIVED"

    diag = {
        "schema": "amphora.ip-fto-guard.registry-manifest-pin-freshness-diagnostic.v1",
        "study_id": "registry-manifest-pin-freshness-v1",
        "authority": "AUDIT_ONLY",
        "claim_under_attack": (
            "amphora-ip-fto-guard/ip/claim-contract.v1.json and "
            "amphora-ip-fto-guard/evidence/phase0/bundle.v1.json registry_manifest_hash "
            "pin faithfully identifies the amphora-ip-fto-guard module's CURRENT entry "
            "in the live root module-manifest.json, even though the pinned hash is not "
            "byte-equal to the live manifest file's own hash."
        ),
        "refutation_criterion": (
            "REFUTED if (a) the canonicalized amphora-ip-fto-guard manifest entry at the "
            "pinned snapshot differs from the entry at live HEAD, OR (b) any registry "
            "succession record between the pinned snapshot and HEAD lists "
            "'amphora-ip-fto-guard' in its edits. Either observation means a real, "
            "undisclosed edit to this module's manifest row happened after the pin was "
            "set and the pin was never advanced to reflect it -- the same defect class "
            "as PIN-01/PIN-02, just on a field neither of those audits checked."
        ),
        "mutate_manifest_entry_control_active": bool(mutate_manifest_entry),
        "forge_succession_edit_control_active": bool(forge_succession_edit),
        "inputs": {
            "claim_contract_path": "amphora-ip-fto-guard/ip/claim-contract.v1.json",
            "bundle_path": "amphora-ip-fto-guard/evidence/phase0/bundle.v1.json",
            "live_manifest_path": "module-manifest.json",
            "succession_chain_path": "registry/succession-chain.v1.json",
        },
        "live_manifest_sha256": live_manifest_sha256,
        "pinned_hash": pinned_hash,
        "bundle_pinned_hash": bundle_pinned_hash,
        "pins_self_consistent": pins_self_consistent,
        "chain_constants_match_amphora_phase0_reviewer_hardcoded_values": chain_constants_match_rust,
        "pin_known_to_succession_chain": pin_known_to_chain,
        "pin_archive_file_hash_matches_dirname": pin_archive_hash_matches_dirname,
        "checkA_entry_drift": {
            "pinned_snapshot_entry_sha256": pinned_entry_sha,
            "live_head_entry_sha256": live_entry_sha,
            "entries_identical": entries_identical,
            "pinned_entry": pinned_entry,
            "live_entry": live_entry,
        },
        "checkB_succession_edits_since_pin": {
            "records_touching_module_between_pin_and_head": touching_records,
            "no_succession_edit_since_pin": no_succession_edit_since_pin,
        },
        "results": {
            "part_a_refuted_entry_drift": part_a_refuted,
            "part_b_refuted_succession_edit": part_b_refuted,
            "H0_verdict": h0_verdict,
        },
        "does_not_close": [
            "Does not verify any field of module-manifest.json other than the "
            "amphora-ip-fto-guard entry itself.",
            "Does not modify claim-contract.v1.json, bundle.v1.json, module-manifest.json, "
            "or the registry succession chain/records/archive.",
            "Does not establish FTO, patentability, procurement, or legal closure.",
        ],
    }
    return diag


if __name__ == "__main__":
    out_arg = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("diagnostic.json")
    mutate = "--mutate-entry" in sys.argv
    forge = "--forge-edit" in sys.argv
    diag = main(mutate_manifest_entry=mutate, forge_succession_edit=forge)
    out_arg.write_text(json.dumps(diag, indent=2, sort_keys=True))
    print("wrote", out_arg)
    print("H0_verdict", diag["results"]["H0_verdict"])
