#!/usr/bin/env python3
"""Fail-closed file policy for publication and guarded autocommits."""

import argparse
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
import sys


PUBLICATION_MAX = 1 << 20
AUTOCOMMIT_MAX = 10 << 20
COMPILED_SUFFIXES = {
    ".a", ".bin", ".class", ".dll", ".dylib", ".exe", ".o", ".pyc",
    ".pyo", ".so", ".wasm",
}
SECRET_PATH = re.compile(
    r"(^|/)(?:\.env(?:$|\.)|credentials?(?:$|[._-])|id_(?:rsa|ed25519)$|"
    r"private[_-]?key(?:$|[._-])|secrets?(?:$|[._-]))", re.I)
SECRET_PATTERNS = [
    re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh" + r"[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk" + r"-(?:ant|proj)-[A-Za-z0-9_-]{16,}\b"),
]
PUBLICATION_FORBIDDEN = (
    ".amphora/**",
    ".github/workflows/**",
    "**/__pycache__/**",
    "**/*.bak",
    "**/*.bak.*",
    "logs/**",
    "state/**",
    "module-queue.json",
)


def git(repo, *args, input_bytes=None, check=True):
    return subprocess.run(
        ["git", "-C", str(repo), *args], input=input_bytes,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


def status_paths(repo):
    raw = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    records = raw.split(b"\0")
    paths = []
    i = 0
    while i < len(records):
        rec = records[i]
        i += 1
        if not rec:
            continue
        text = rec.decode("utf-8", "surrogateescape")
        status, path = text[:2], text[3:]
        if "R" in status or "C" in status:
            i += 1  # second NUL record is the old path
        paths.append((status, path))
    return paths


def staged_paths(repo):
    raw = git(repo, "diff", "--cached", "--name-status", "-z", "--diff-filter=ACDMRTUXB").stdout
    records = raw.split(b"\0")
    paths = []
    i = 0
    while i < len(records):
        status_raw = records[i]
        i += 1
        if not status_raw:
            continue
        status = status_raw.decode("ascii", "replace")
        path = records[i].decode("utf-8", "surrogateescape")
        i += 1
        if status.startswith(("R", "C")):
            path = records[i].decode("utf-8", "surrogateescape")
            i += 1
        paths.append((status[:1], path))
    return paths


def evaluate(repo, entries, profile):
    violations = []
    approved = []
    max_size = PUBLICATION_MAX if profile == "publication" else AUTOCOMMIT_MAX
    for status, rel in entries:
        reasons = []
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts or "\n" in rel or "\r" in rel:
            reasons.append("unsafe-path")
        if rel == ".git" or rel.startswith(".git/"):
            reasons.append("git-internals")
        if SECRET_PATH.search(rel):
            reasons.append("secret-bearing-path")
        if profile == "publication" and any(fnmatch.fnmatch(rel, pat) for pat in PUBLICATION_FORBIDDEN):
            reasons.append("publication-forbidden-path")
        if path.suffix.lower() in COMPILED_SUFFIXES:
            reasons.append("compiled-binary-suffix")
        if profile == "autocommit" and status in {"D", "R", "C"}:
            reasons.append("autocommit-refuses-delete-or-rename")

        full = repo / path
        if full.exists() and full.is_symlink():
            reasons.append("symlink")
        if full.exists() and full.is_file():
            size = full.stat().st_size
            if size > max_size:
                reasons.append("oversized:%d" % size)
            data = full.read_bytes()
            if b"\0" in data[:8192]:
                reasons.append("binary-content")
            text = data.decode("utf-8", "replace")
            if any(rx.search(text) for rx in SECRET_PATTERNS):
                reasons.append("credential-pattern")
        if reasons:
            violations.append({"path": rel, "status": status, "reasons": reasons})
        else:
            approved.append(rel)
    return approved, violations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--profile", choices=("publication", "autocommit"), default="publication")
    parser.add_argument("--source", choices=("staged", "worktree"), default="staged")
    parser.add_argument("--stage-approved", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    entries = staged_paths(repo) if args.source == "staged" else status_paths(repo)
    approved, violations = evaluate(repo, entries, args.profile)
    if args.stage_approved:
        if args.source != "worktree" or args.profile != "autocommit":
            parser.error("--stage-approved requires --source worktree --profile autocommit")
        for rel in approved:
            git(repo, "add", "--", rel)
    result = {"profile": args.profile, "source": args.source,
              "approved": approved, "violations": violations}
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        print()
    else:
        for row in violations:
            print("BLOCK %s: %s" % (row["path"], ",".join(row["reasons"])), file=sys.stderr)
        print("approved=%d blocked=%d" % (len(approved), len(violations)))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
