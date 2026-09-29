"""A fresh CLI process must not depend on pytest's prior import order."""

import subprocess
import sys


def test_runtime_entrypoint_starts_in_an_uninitialized_interpreter():
    result = subprocess.run([sys.executable, "-I", "-m", "amphora_campaign_runtime", "--help"],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "coordinate" in result.stdout and "--config" in result.stdout
