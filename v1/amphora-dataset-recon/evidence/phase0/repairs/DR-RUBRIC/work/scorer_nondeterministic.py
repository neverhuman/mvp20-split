#!/usr/bin/env python3
"""POSITIVE-CONTROL DEFECT COPY of scorer.py -- deliberately planted for the
DR-RUBRIC two-replay determinism attack. The only change from scorer.py is
the addition of a wall-clock 'generated_at' timestamp field to the output
payload, which makes two runs over the identical input byte-differ. This
file exists ONLY to prove the two-replay SHA-256 gate has the power to
detect a real non-determinism defect; it is never used to score a real
candidate and never cited as a deliverable.
"""
import json
import sys
import time

sys.path.insert(0, ".")
from scorer import run  # noqa: E402


if __name__ == "__main__":
    rubric_path, snapshot_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    out = run(rubric_path, snapshot_path)
    out["generated_at"] = time.time()  # PLANTED DEFECT: wall-clock -> non-deterministic bytes
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
    print("WROTE", out_path)
