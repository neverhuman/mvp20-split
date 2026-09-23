#!/usr/bin/env python3
"""
Builds a tempdir copy of amphora-public-corrosion-benchmark's evidence tree
(evidence/audit/, evidence/phase0/kpis/, evidence/phase0/repairs/*/done/)
and plants exactly one defect of the kind check_index_completeness.py exists
to catch: the on-disk receipt for eis-rustcreep-crossmodality-v1 is left
untouched, but its entry is deleted from the copied live index's
(evidence/phase0/repairs/R-N03/done/audit-verdicts-consolidated-kpi.v3.dsse.json)
audit_verdicts_index -- simulating a receipt that landed on disk without the
index being rebuilt to reference it (the recurring defect). No file under
the real module tree is touched; this only ever writes under the tempdir.
"""
import base64
import glob
import hashlib
import json
import os
import shutil
import sys

MODULE_ROOT = "/home/ubuntu/amphora/build/mvp20-split/amphora-public-corrosion-benchmark"
TARGET_RECEIPT_PATH = "evidence/audit/eis-rustcreep-crossmodality-v1/eis-rustcreep-crossmodality-receipt.v1.dsse.json"
LIVE_INDEX_REL = "evidence/phase0/repairs/R-N03/done/audit-verdicts-consolidated-kpi.v3.dsse.json"


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main(tmproot):
    if os.path.exists(tmproot):
        shutil.rmtree(tmproot)
    os.makedirs(tmproot)

    # Mirror only the subtrees the checker actually reads.
    for sub in ["evidence/audit", "evidence/phase0/kpis", "evidence/phase0/repairs"]:
        src = os.path.join(MODULE_ROOT, sub)
        dst = os.path.join(tmproot, sub)
        if os.path.isdir(src):
            shutil.copytree(src, dst)

    live_index_copy = os.path.join(tmproot, LIVE_INDEX_REL)
    pre_sha256 = sha256_bytes(open(live_index_copy, "rb").read())

    d = json.load(open(live_index_copy))
    env = d["signature"]
    payload = json.loads(base64.b64decode(env["payload"]))

    before_n = len(payload["audit_verdicts_index"])
    before_paths = sorted(e.get("receipt_path") for e in payload["audit_verdicts_index"])
    assert TARGET_RECEIPT_PATH in before_paths, "target receipt not present in live index copy pre-mutation"

    payload["audit_verdicts_index"] = [
        e for e in payload["audit_verdicts_index"] if e.get("receipt_path") != TARGET_RECEIPT_PATH
    ]
    after_n = len(payload["audit_verdicts_index"])
    assert after_n == before_n - 1

    new_payload_bytes = json.dumps(payload).encode()
    env["payload"] = base64.b64encode(new_payload_bytes).decode()
    # NOTE: signatures[] are now stale/invalid against the mutated payload by
    # construction -- this checker does not verify signatures (see its own
    # docstring), only completeness, so that is expected and out of scope.
    d["signature"] = env
    open(live_index_copy, "w").write(json.dumps(d, indent=2, sort_keys=True))
    post_sha256 = sha256_bytes(open(live_index_copy, "rb").read())

    on_disk_receipt_still_present = os.path.exists(os.path.join(tmproot, TARGET_RECEIPT_PATH))

    summary = {
        "tmproot": tmproot,
        "live_index_rel": LIVE_INDEX_REL,
        "live_index_pre_mutation_sha256": pre_sha256,
        "live_index_post_mutation_sha256": post_sha256,
        "target_receipt_path": TARGET_RECEIPT_PATH,
        "target_receipt_still_on_disk_in_tmpdir": on_disk_receipt_still_present,
        "audit_verdicts_index_count_before": before_n,
        "audit_verdicts_index_count_after": after_n,
        "how_planted": (
            "Copied evidence/audit, evidence/phase0/kpis, evidence/phase0/repairs verbatim "
            "into a tempdir, then edited the DSSE payload of the copied live index file (%s) "
            "to remove the single audit_verdicts_index entry whose receipt_path == %r "
            "(entries %d -> %d), re-base64'd the payload in place, left signatures[] "
            "byte-unchanged (now stale/invalid, which is expected and irrelevant to this "
            "completeness-only check), and left the on-disk receipt file for that audit "
            "completely untouched." % (LIVE_INDEX_REL, TARGET_RECEIPT_PATH, before_n, after_n)
        ),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/r-s07-positive-control")
