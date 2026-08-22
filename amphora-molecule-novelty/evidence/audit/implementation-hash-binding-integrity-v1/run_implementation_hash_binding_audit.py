#!/usr/bin/env python3
"""Implementation-source-hash-binding-integrity audit, scoped to amphora-molecule-novelty.

Attacks the standing claim in this module's OWN docs (docs/mission.md +
docs/capability-profile.json) that three named source artifacts are bound to
specific SHA-256 hashes:
  1. implementation:    amphora-molecule-capabilities/src/lib.rs
  2. version_source:     amphora-molecule-capabilities/Cargo.toml
  3. registry (adapter): amphora-engine/src/lib.rs

capability-profile.json's own "automatic_demotion" list names "source hash
mutation" as a trigger, so this binding is load-bearing by the module's own
declared policy, not incidental prose.

A same-day sibling fire (fire_id 20260816T130001-3022527-0af70e0219bf,
module amphora-molecule-generator) already found the implementation hash
stale for amphora-molecule-generator's own citations of the SAME shared file
and explicitly logged the same stale hash appearing in amphora-molecule-novelty's
docs too, but scoped fixing/verifying that out of its own fire ("context only,
out of this module's scope to fix"). This audit is the in-scope follow-through
for amphora-molecule-novelty: (a) it independently re-derives the mismatch
rather than trusting the sibling fire's numbers, (b) it extends coverage to
the two hash citations the sibling fire never checked at all
(version_source_sha256, registry_sha256), and (c) it establishes WHEN the
mismatch originated (inception vs later drift) via git blob history, which
the sibling fire did not attempt.

Falsifying observation sought: any of the three claimed hashes matching the
current file content AND matching the git HEAD blob AND the working tree
having no uncommitted diff -- i.e. genuine unrecorded drift or a typo that
self-corrects on inspection would refute "this citation is currently wrong".
Conversely, finding the mismatch reproduces AND coincides with a clean git
status AND a single-commit file history refutes the weaker, more charitable
hypothesis (drift after correct baseline) in favor of the stronger one: the
citation was never correct, from the very commit that introduced it.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-novelty"
MISSION = MOD / "docs/mission.md"
PROFILE = MOD / "docs/capability-profile.json"

TARGETS = [
    {
        "label": "implementation",
        "path": "amphora-molecule-capabilities/src/lib.rs",
        "claimed_field": "evidence_inventory.implementation.sha256",
    },
    {
        "label": "version_source",
        "path": "amphora-molecule-capabilities/Cargo.toml",
        "claimed_field": "evidence_inventory.implementation.version_source_sha256",
    },
    {
        "label": "registry",
        "path": "amphora-engine/src/lib.rs",
        "claimed_field": "evidence_inventory.runtime_integration.registry_sha256",
    },
]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def git_blob_bytes(rel_path, ref="HEAD"):
    # NB: must not go through text=True/.strip() -- that silently mutates
    # trailing-newline bytes and corrupts the hash of the retrieved blob.
    return subprocess.run(
        ["git", "show", f"{ref}:{rel_path}"], cwd=ROOT, capture_output=True, check=True
    ).stdout


def get_field(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        cur = cur[part]
    return cur


def main():
    profile = json.loads(PROFILE.read_text())
    mission_text = MISSION.read_text()

    checks = {}
    findings = []

    for t in TARGETS:
        rel = t["path"]
        abspath = ROOT / rel
        working_bytes = abspath.read_bytes()
        actual_working_sha = sha(working_bytes)

        git_status = git("status", "--porcelain", "--", rel)
        head_blob = git_blob_bytes(rel, "HEAD")
        actual_head_sha = sha(head_blob)

        commit_count = git("log", "--oneline", "--", rel)
        n_commits = len([l for l in commit_count.splitlines() if l.strip()])
        first_commit = commit_count.splitlines()[-1].split()[0] if commit_count else None

        claimed_sha = get_field(profile, t["claimed_field"])

        # cross-check the identical value is repeated in mission.md prose
        # (only the implementation hash is quoted in mission.md; the other
        # two are capability-profile.json-only fields)
        in_mission_md = claimed_sha in mission_text

        working_matches_claim = actual_working_sha == claimed_sha
        head_matches_working = actual_head_sha == actual_working_sha
        git_clean = git_status == ""

        checks[t["label"]] = {
            "path": rel,
            "claimed_field": t["claimed_field"],
            "claimed_sha256": claimed_sha,
            "actual_working_tree_sha256": actual_working_sha,
            "actual_git_head_blob_sha256": actual_head_sha,
            "git_status_porcelain": git_status,
            "git_working_tree_clean_for_this_file": git_clean,
            "git_head_blob_matches_working_tree": head_matches_working,
            "n_commits_touching_file": n_commits,
            "introducing_commit": first_commit,
            "claimed_sha_also_quoted_in_mission_md": in_mission_md,
            "working_tree_matches_claimed_hash": working_matches_claim,
        }

        if not working_matches_claim:
            findings.append(t["label"])

    # interpret: for each mismatched target, since git_clean is True and
    # head_matches_working is True and n_commits==1, the claimed hash was
    # wrong AT THE INTRODUCING COMMIT, not a later drift.
    inception_wrong = []
    for label in findings:
        c = checks[label]
        if c["git_working_tree_clean_for_this_file"] and c["git_head_blob_matches_working_tree"] and c["n_commits_touching_file"] == 1:
            inception_wrong.append(label)

    automatic_demotion_triggers = profile.get("automatic_demotion", [])
    source_hash_mutation_is_declared_trigger = "source hash mutation" in automatic_demotion_triggers

    result = {
        "schema": "amphora.molecule-novelty-implementation-hash-binding-audit.v1",
        "module_id": "amphora-molecule-novelty",
        "attack": "implementation-source-hash-binding-integrity audit (novelty-scoped, 3-citation coverage)",
        "targets_checked": [t["label"] for t in TARGETS],
        "checks": checks,
        "n_targets_checked": len(TARGETS),
        "n_mismatched": len(findings),
        "mismatched_labels": findings,
        "n_mismatched_wrong_since_inception": len(inception_wrong),
        "mismatched_wrong_since_inception_labels": inception_wrong,
        "capability_profile_automatic_demotion_triggers": automatic_demotion_triggers,
        "source_hash_mutation_is_declared_automatic_demotion_trigger": source_hash_mutation_is_declared_trigger,
        "policy_self_contradiction": (
            source_hash_mutation_is_declared_trigger and len(findings) > 0
        ),
        "checks_all_pass": len(findings) == 0,
    }
    return result


if __name__ == "__main__":
    import sys
    out_path = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    result = main()
    Path(out_path).write_text(json.dumps(result, sort_keys=True, indent=2))
    print("WROTE", out_path)
    print("n_mismatched:", result["n_mismatched"], "of", result["n_targets_checked"])
    print("wrong_since_inception:", result["mismatched_wrong_since_inception_labels"])
