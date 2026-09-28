"""Test-only computation barrier around actual installed tool/SDK execution."""

import importlib
import importlib.util
import json
import sys
import time
from pathlib import Path

from amphora_tool_protocol import ProtocolError, run_worker


def main():
    module, config_path, mode, marker_path = sys.argv[1:]
    assert module in {"amphora_numeric_affine", "amphora_sequence_statistics"}
    metadata = importlib.import_module(module + ".metadata")
    adapter = importlib.import_module(module + ".adapter")
    assert Path(adapter.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
    assert importlib.util.find_spec("sqlalchemy") is None
    assert importlib.util.find_spec("amphora_campaign_runtime") is None
    assert importlib.util.find_spec("amphora_data_artifacts") is None

    def compute(payload):
        if mode == "expire":
            Path(marker_path).write_text(json.dumps({"stage": "before_compute", "module": module}), encoding="utf-8")
            assert sys.stdin.readline().strip() == "continue"
            time.sleep(0.05)
        return adapter.execute(payload)

    try:
        print(json.dumps(run_worker(config_path, metadata.descriptor, compute)), flush=True)
    except ProtocolError:
        print(json.dumps({"status": "authority_or_transport_lost"}), flush=True)
        raise SystemExit(3) from None


if __name__ == "__main__":
    main()
