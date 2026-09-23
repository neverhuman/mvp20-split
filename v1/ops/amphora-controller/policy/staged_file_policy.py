#!/usr/bin/env python3
"""Fail-closed file policy for publication and guarded autocommits."""

import argparse
import fnmatch
import hashlib
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
BINARY_DATA_SUFFIXES = {
    ".7z", ".arrow", ".avro", ".bz2", ".ckpt", ".db", ".docx", ".feather",
    ".gz", ".h5", ".hdf5", ".joblib", ".jpeg", ".jpg", ".lz4", ".npy",
    ".npz", ".onnx", ".parquet", ".pdf", ".pickle", ".pkl", ".png", ".pt",
    ".pth", ".rar", ".safetensors", ".sqlite", ".tar", ".tgz", ".whl", ".xz",
    ".zip", ".zst",
}
NEW_DATA_SUFFIXES = {
    ".csv", ".jsonl", ".ndjson", ".parquet", ".tsv", ".xls", ".xlsx",
}
NEW_DATA_SEGMENT = re.compile(r"(^|/)(?:data|datasets?|derived|objects|quarantine|raw|splits)(/|$)", re.I)
REVIEWED_MUTABLE_DATA_PATHS = {
    "ops/amphora-controller/bootstrap/data-acquisition-queue.jsonl",
}
SECRET_PATH = re.compile(
    r"(^|/)(?:\.env(?:$|\.)|\.netrc$|\.npmrc$|\.pypirc$|authorized_keys$|"
    r"credentials?(?:$|[._-])|id_(?:rsa|ed25519)$|kubeconfig(?:$|[._-])|"
    r"private[_-]?key(?:$|[._-])|secrets?(?:$|[._-])|service[_-]?account(?:$|[._-]))",
    re.I)
SECRET_PATTERNS = [
    re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh" + r"[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk" + r"-(?:ant|proj)-[A-Za-z0-9_-]{16,}\b"),
]
PINNED_BINARY_EVIDENCE = {
    "amphora-known-answer-benchmarks/evidence/phase0/repairs/V-A05/work/a221_verify.pdf": "fa2e8ff6973a1fb18189565653d762772333f62f8c6d079017ee9f3be376dc6f",
    "amphora-viscosity-score/evidence/audit/arrhenius-extrapolation-domain-gap-v1/glycerine-producers-association-1963-dorsey-viscosity-table-source.pdf": "e5b1c4cbfa174cee39ab482164aaa07513fd9f976d33e9a9457876a93b95c3db",
    "amphora-viscosity-score/evidence/audit/arrhenius-fixture-source-provenance-v1/glycerinWaterViscosity_Dorsey_mirror.pdf": "e5b1c4cbfa174cee39ab482164aaa07513fd9f976d33e9a9457876a93b95c3db",
    "amphora-viscosity-score/evidence/phase0/repairs/W-VISC1/attempts/krieger-dougherty-ccby-reachability-probe-v1/fig8.jpg": "e0973c5b7b6a985e0243987529820cd139a8e56f7d2353a27d4e987eaff2120a",
    "docs/directives/2026-08-05-closing-the-open-portfolio.docx": "650e48c503de0acdebb33e1adc956b6d695b7fd22500d8c44f62a507c9be9322",
}
PUBLICATION_FORBIDDEN = (
    ".amphora/**",
    ".github/workflows/**",
    "feedback/**",
    "**/reference/**/feedback*/raw/**",
    "**/reference/**/feedback*/derived/**",
    "**/reference/**/feedback*/objects/**",
    "**/reference/**/feedback*/splits/**",
    "**/reference/**/quarantine/**/raw/**",
    "**/reference/**/quarantine/**/derived/**",
    "**/reference/**/quarantine/**/objects/**",
    "**/reference/**/quarantine/**/splits/**",
    "**/__pycache__/**",
    "**/*.bak",
    "**/*.bak.*",
    "logs/**",
    "state/**",
    "module-queue.json",
)


def omitted_dataset_paths(repo, source="worktree"):
    """Return payload paths from both HEAD and the bytes under review.

    Taking the union makes a manifest-row deletion unable to authorize that same
    payload in one staged change. A deliberate retirement therefore needs a prior
    reviewed commit before the policy can stop recognizing the old path.
    """
    manifests = []
    committed = git(repo, "show", "HEAD:DATASETS.local.json", check=False)
    if committed.returncode == 0:
        manifests.append(committed.stdout)
    if source == "staged":
        manifest_bytes = entry_bytes(repo, "DATASETS.local.json", source)
    else:
        manifest = repo / "DATASETS.local.json"
        manifest_bytes = manifest.read_bytes() if manifest.is_file() else None
    if manifest_bytes is not None:
        manifests.append(manifest_bytes)
    if not manifests:
        return set()
    try:
        paths = set()
        for manifest_bytes in manifests:
            rows = json.loads(manifest_bytes)["omitted"]
            paths.update(
                row["path"] for row in rows
                if row.get("size_bytes", 0) > 0 and isinstance(row.get("path"), str)
            )
        return paths
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("DATASETS.local.json is malformed: %s" % exc) from exc


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
        status_pair, path = text[:2], text[3:]
        if "R" in status_pair or "C" in status_pair:
            i += 1  # second NUL record is the old path
        status = status_pair[0] if status_pair[0] != " " else status_pair[1]
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


def tracked_paths(repo):
    raw = git(repo, "ls-files", "-z").stdout
    return [("T", path.decode("utf-8", "surrogateescape"))
            for path in raw.split(b"\0") if path]


def entry_bytes(repo, rel, source):
    """Read exactly the bytes being reviewed, not a different worktree copy."""
    if source == "staged":
        proc = git(repo, "show", ":%s" % rel, check=False)
        return proc.stdout if proc.returncode == 0 else None
    full = repo / rel
    return full.read_bytes() if full.exists() and full.is_file() else None


def entry_is_symlink(repo, rel, source):
    if source == "staged":
        raw = git(repo, "ls-files", "-s", "-z", "--", rel, check=False).stdout
        return raw.startswith(b"120000 ")
    return (repo / rel).is_symlink()


def evaluate(repo, entries, profile, source="worktree"):
    violations = []
    approved = []
    max_size = PUBLICATION_MAX if profile == "publication" else AUTOCOMMIT_MAX
    excluded_datasets = omitted_dataset_paths(repo, source) if profile == "publication" else set()
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
        if profile == "publication" and rel in excluded_datasets:
            reasons.append("inventoried-dataset-payload")
        if profile == "publication" and status in {"A", "M", "R", "C"} and (
                NEW_DATA_SEGMENT.search(rel) or path.suffix.lower() in NEW_DATA_SUFFIXES
                ) and rel not in REVIEWED_MUTABLE_DATA_PATHS:
            reasons.append("new-data-class-path-requires-reviewed-policy-pin")
        if path.suffix.lower() in COMPILED_SUFFIXES:
            reasons.append("compiled-binary-suffix")
        if profile == "autocommit" and status in {"D", "R", "C"}:
            reasons.append("autocommit-refuses-delete-or-rename")

        if entry_is_symlink(repo, rel, source):
            reasons.append("symlink")
        data = entry_bytes(repo, rel, source)
        if source == "tracked" and data is None:
            reasons.append("tracked-path-missing")
        if data is not None:
            digest = hashlib.sha256(data).hexdigest()
            size = len(data)
            if size > max_size:
                reasons.append("oversized:%d" % size)
            pinned = PINNED_BINARY_EVIDENCE.get(rel)
            if path.suffix.lower() in BINARY_DATA_SUFFIXES and pinned != digest:
                reasons.append("binary-data-suffix")
            if b"\0" in data[:8192]:
                if pinned != digest:
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
    parser.add_argument("--source", choices=("staged", "tracked", "worktree"), default="staged")
    parser.add_argument("--stage-approved", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.source == "staged":
        entries = staged_paths(repo)
    elif args.source == "tracked":
        entries = tracked_paths(repo)
    else:
        entries = status_paths(repo)
    approved, violations = evaluate(repo, entries, args.profile, args.source)
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
