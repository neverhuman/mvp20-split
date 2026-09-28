"""Ordinary artifact startup cannot opt into the explicit test process hooks."""

import json

import pytest
from amphora_data_artifacts.hosting import Host


def test_ordinary_artifact_configuration_rejects_fault_switch(tmp_path):
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps({"fault": "upload_synced"}))
    with pytest.raises(ValueError, match="Unknown configuration"):
        Host.load(path)
