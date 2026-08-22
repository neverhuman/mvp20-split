from __future__ import annotations

import json
import os
from pathlib import Path
import socket

import pandas as pd


def denied(action) -> bool:
    try:
        action()
    except (OSError, PermissionError):
        return True
    return False


checks = {
    "network_denied": denied(lambda: socket.create_connection(("1.1.1.1", 53), timeout=1)),
    "host_secret_environment_absent": not any(
        any(token in name.upper() for token in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))
        for name in os.environ
    ),
    "public_training_labels_absent": not {
        "formation_energy_ev_natom",
        "bandgap_energy_ev",
    }.intersection(pd.read_csv("/inputs/train_public.csv", nrows=1).columns),
    "public_test_labels_absent": not {
        "formation_energy_ev_natom",
        "bandgap_energy_ev",
    }.intersection(pd.read_csv("/inputs/test_public.csv", nrows=1).columns),
    "forbidden_host_label_file_absent": not Path(
        "/home/ubuntu/nomad/labeled_test.csv"
    ).exists(),
    "root_filesystem_write_denied": denied(
        lambda: Path("/should-not-write").write_text("blocked", encoding="utf-8")
    ),
    "shadow_read_denied": denied(lambda: Path("/etc/shadow").read_text(encoding="utf-8")),
}
Path("/output/write_probe.txt").write_text("allowed output only\n", encoding="utf-8")
checks["fresh_output_write_allowed"] = Path("/output/write_probe.txt").is_file()
receipt = {"checks": checks, "uid": os.getuid(), "gid": os.getgid()}
Path("/output/receipt.json").write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
if not all(checks.values()) or os.getuid() == 0:
    raise SystemExit(1)
