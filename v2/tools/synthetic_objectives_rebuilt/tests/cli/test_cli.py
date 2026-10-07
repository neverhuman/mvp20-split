import json
import subprocess
import sys

from amphora_synthetic_objectives_rebuilt.metadata import policy_bytes, schema_bytes


def test_offline_cli_math_and_safe_error(fixture_request, tmp_path):
    policy = tmp_path / "policy.json"
    policy.write_bytes(policy_bytes())
    command = [sys.executable, "-m", "amphora_synthetic_objectives_rebuilt", "compute", "--image-sha256", "b" * 64,
               "--policy-file", str(policy)]
    passed = subprocess.run(command, input=fixture_request.model_dump_json().encode(), capture_output=True, check=True, timeout=30)
    assert [o["value"] for o in json.loads(passed.stdout)["outcome"]["objectives"]] == [5.0, 9.0]
    assert not passed.stderr and not passed.stdout.endswith(b"\n")
    failed = subprocess.run(command, input=b"private-fixture", capture_output=True, check=False, timeout=30)
    assert failed.returncode == 2 and not failed.stdout
    assert failed.stderr.strip() == b"invalid_synthetic_input_or_configuration"


def test_policy_schema_and_descriptor_commands():
    base = [sys.executable, "-m", "amphora_synthetic_objectives_rebuilt"]
    result = subprocess.run([*base, "policy"], capture_output=True, check=True, timeout=30)
    assert result.stdout == policy_bytes()
    result = subprocess.run([*base, "schema", "--kind", "policy"], capture_output=True, check=True, timeout=30)
    assert result.stdout == schema_bytes("policy")
    result = subprocess.run([*base, "describe", "--image-sha256", "b" * 64], capture_output=True, check=True, timeout=30)
    assert len(json.loads(result.stdout)["tool"]["inputs"]) == 2
