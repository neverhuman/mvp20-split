import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from amphora_sequence_space import OPERATOR, PROFILE
from amphora_sequence_space.adapter import SpaceWorkerAdapter
from amphora_sequence_space.capability import SpaceCapability
from amphora_tool_protocol import ToolInputRejected

ROOT = Path(__file__).absolute().parents[4]


def payload():
    data = json.loads(
        (Path(__file__).parent.parent / "legality/request.json").read_bytes()
    )
    data["source"]["profile"] = PROFILE.model_dump(mode="json")
    data["operator"] = OPERATOR.model_dump(mode="json")
    return json.dumps(data).encode()


def test_descriptor_and_schema_bytes_match_publication():
    capability = SpaceCapability()
    descriptor = capability.descriptor("c" * 64)
    assert descriptor.tool.binding.release == "0.2.0"
    assert descriptor.tool.binding.capability_id == "synthetic.sequence-move"
    assert "synthetic-tests" in descriptor.tool.applicability
    assert descriptor.authority_ceiling == "synthetic_only"
    for direction in ("input", "output"):
        reference = capability.schema_ref(direction)
        raw = capability.schema_bytes(direction)
        assert hashlib.sha256(raw).hexdigest() == reference.sha256
        assert (
            raw
            == (
                ROOT
                / "contracts/schemas/v1"
                / (reference.schema_id + ".validation.json")
            ).read_bytes()
        )
    with pytest.raises(ValueError):
        capability.schema_bytes("other")


def test_bound_adapter_executes_and_cannot_rebind():
    adapter = SpaceWorkerAdapter()
    with pytest.raises(ToolInputRejected):
        adapter.execute(payload())
    first = adapter.descriptor("c" * 64)
    assert adapter.descriptor("c" * 64) == first
    with pytest.raises(ValueError, match="image_changed"):
        adapter.descriptor("d" * 64)
    result = adapter.execute(payload())
    assert not result.endswith(b"\n")
    assert json.loads(result)["result"]["kind"] == "sequence"
    assert result == adapter.execute(payload())


@pytest.mark.parametrize(
    "raw",
    [b"{}", b"x" * 262145, "text", b'{"private":"never-echo-this"}'],
    ids=["missing", "capacity", "wrong-type", "safe-rejection"],
)
def test_invalid_input_is_closed_and_safe(raw):
    adapter = SpaceWorkerAdapter()
    adapter.descriptor("c" * 64)
    with pytest.raises(ToolInputRejected) as error:
        adapter.execute(raw)
    assert error.value.reason_code == "invalid_sequence_space_move"
    assert "never-echo-this" not in str(error.value)


def test_public_cli_compute_profiles_and_safe_error():
    def cli(*arguments, body=None):
        return subprocess.run(
            [sys.executable, "-m", "amphora_sequence_space", *arguments],
            input=body,
            capture_output=True,
            check=False,
            timeout=30,
        )

    profiles = cli("profiles")
    assert profiles.returncode == 0
    assert json.loads(profiles.stdout) == {
        "profile": PROFILE.model_dump(mode="json"),
        "operator": OPERATOR.model_dump(mode="json"),
    }
    computed = cli("compute", "--image-sha256", "c" * 64, body=payload())
    assert (
        computed.returncode == 0
        and json.loads(computed.stdout)["result"]["kind"] == "sequence"
    )
    adapter = SpaceWorkerAdapter()
    adapter.descriptor("c" * 64)
    assert computed.stdout == adapter.execute(payload())
    rejected = cli(
        "compute", "--image-sha256", "c" * 64, body=b'{"private":"never-echo-this"}'
    )
    assert rejected.returncode == 2 and rejected.stdout == b""
    assert rejected.stderr.strip() == b"invalid_sequence_input_or_configuration"
