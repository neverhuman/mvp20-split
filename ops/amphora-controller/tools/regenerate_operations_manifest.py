#!/usr/bin/env python3
"""Regenerate OPERATIONS.local.json from committed freeze/bootstrap evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--source-history-commits", type=int, required=True)
    parser.add_argument("--captured-at", required=True)
    parser.add_argument("--legacy-archive", required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    controller = repo / "ops" / "amphora-controller"
    bootstrap = controller / "bootstrap"
    checkpoint = json.loads((bootstrap / "campaign-chain-checkpoint.json").read_text())
    freeze = json.loads((bootstrap / "freeze" / "record.json").read_text())
    frozen = []
    for name in ("campaign.json", "data-acquisition-queue.jsonl",
                 "campaign-chain-checkpoint.json"):
        path = bootstrap / name
        frozen.append({"path": path.relative_to(repo).as_posix(),
                       "size_bytes": path.stat().st_size, "sha256": sha(path)})
    archive_manifest = bootstrap / "freeze" / "cron-legacy.MANIFEST.json"
    doc = {
        "schema": "amphora.operations.local.v1",
        "captured_at": args.captured_at,
        "xbabe2_source": {
            "host": "xbabe2", "path": "/home/ubuntu/amphora/build/mvp20-split",
            "final_git_sha": args.source_sha,
            "history_commits": args.source_history_commits,
            "github_history_included": False,
        },
        "xbabe1_legacy_controller": {
            "source_path": "/home/ubuntu/amphora-cron",
            "source_git_sha": checkpoint["source"]["git_sha"],
            "source_history_commits": 35,
            "legacy_archive": args.legacy_archive,
            "archive_manifest": (archive_manifest.relative_to(repo).as_posix()
                                 if archive_manifest.exists() else None),
            "archive_manifest_sha256": sha(archive_manifest) if archive_manifest.exists() else None,
        },
        "frozen_bootstrap": frozen,
        "freeze_record": {
            "path": "ops/amphora-controller/bootstrap/freeze/record.json",
            "sha256": sha(bootstrap / "freeze" / "record.json"),
            "hard_stop_tag": freeze["tag"],
        },
        "excluded_from_github": [
            "xbabe1 legacy .git directory and its 35-commit history",
            "runtime logs and counters", "credentials and signing seeds",
            "stale backups", "unused module-queue.json",
            "two malformed newline-bearing filenames", "full lane history"
        ],
        "deployment": {
            "xbabe1_checkout": "/home/ubuntu/mvp20-split",
            "xbabe1_mutable_state": "/home/ubuntu/amphora-cron",
            "config": "/home/ubuntu/.config/amphora/mvp20-cron.env",
            "github_deploy_key": "dedicated read-only repository deploy key",
        },
        "state": "INTENTIONALLY_PAUSED",
        "activation_requires_explicit_user_approval": True,
    }
    (repo / "OPERATIONS.local.json").write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print("regenerated OPERATIONS.local.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
