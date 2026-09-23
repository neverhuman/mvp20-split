#!/usr/bin/env python3
"""Summarise a `cargo test --workspace` log into the acceptance block."""
import json
import re
import sys
from pathlib import Path

log = Path(sys.argv[1])
text = log.read_text(errors="replace")
suites = 0
passed = failed = ignored = 0
for m in re.finditer(r"^test result: (ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored",
                     text, re.M):
    suites += 1
    passed += int(m.group(2))
    failed += int(m.group(3))
    ignored += int(m.group(4))
failing = sorted(set(re.findall(r"^\s{4}(\S+)$", text, re.M))) if failed else []
out = {
    "command": ("RDKIT_INCLUDE_DIR/RDKIT_LIB_DIR/BOOST_INCLUDE_DIR/LD_LIBRARY_PATH from "
                "/home/ubuntu/.local/share/amphora/rdkit-2026.03.2; "
                "flock -w 300 .cron.lock ~/.cargo/bin/cargo test --workspace --locked "
                "--features rdkit"),
    "toolchain": "1.96.0 (rust-toolchain.toml)",
    "exit_code": int(sys.argv[2]),
    "suites": suites,
    "tests_passed": passed,
    "tests_failed": failed,
    "tests_ignored": ignored,
    "failing_tests": failing,
}
print(json.dumps(out, indent=2, sort_keys=True))
