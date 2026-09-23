#!/usr/bin/env python3
"""Generate or verify the deployed controller's complete SHA-256 inventory."""

import argparse
import hashlib
from pathlib import Path
import sys


MANIFEST = "controller-tree.sha256"


# Regenerable bytecode caches. Any successor who runs a Python file in this tree
# creates one; without this filter the next `verify` fails with a mismatch that
# looks like tampering. They are also already ignored by .gitignore, so including
# them would make the deployed manifest disagree with a fresh clone.
IGNORED_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}


def files(root):
    return sorted(path for path in root.rglob("*")
                  if path.is_file() and not path.is_symlink() and path.name != MANIFEST
                  and IGNORED_DIRS.isdisjoint(path.relative_to(root).parts))


def rows(root):
    return [(hashlib.sha256(path.read_bytes()).hexdigest(), path.relative_to(root).as_posix())
            for path in files(root)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("generate", "verify"))
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = root / MANIFEST
    actual = rows(root)
    if args.mode == "generate":
        manifest.write_text("".join("%s  %s\n" % row for row in actual))
        print("wrote %s (%d files)" % (manifest, len(actual)))
        return 0
    try:
        expected = [tuple(line.split("  ", 1)) for line in manifest.read_text().splitlines() if line]
    except FileNotFoundError:
        print("missing %s" % manifest, file=sys.stderr)
        return 1
    if expected != actual:
        print("controller manifest mismatch", file=sys.stderr)
        return 1
    print("controller manifest verified (%d files)" % len(actual))
    return 0


if __name__ == "__main__":
    sys.exit(main())
