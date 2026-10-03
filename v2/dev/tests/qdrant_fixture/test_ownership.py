"""Fixture resource operations require exact labels and pinned container identity."""

import json

import pytest
import qdrant_fixture as fixture


@pytest.mark.parametrize("mismatch", ["label", "image", "state-image"])
def test_fixture_rejects_foreign_resources_before_operations(tmp_path, monkeypatch, mismatch):
    state = {
        "container": "fixture-container",
        "volume": "fixture-volume",
        "owner": "fixture-owner",
        "image": fixture.IMAGE,
    }
    if mismatch == "state-image":
        state["image"] = "different"
    path = tmp_path / "state.json"
    path.write_text(json.dumps(state), encoding="utf-8")
    monkeypatch.setattr(fixture, "STATE", path)

    def inspect_only(kind, action, name):
        assert kind in {"container", "volume"} and action == "inspect"
        labels = {fixture.LABEL: "different" if mismatch == "label" else state["owner"]}
        return json.dumps(
            [
                {
                    "Config": {
                        "Labels": labels,
                        "Image": "different" if mismatch == "image" else fixture.IMAGE,
                    },
                    "Labels": labels,
                }
            ]
        )

    monkeypatch.setattr(fixture, "docker", inspect_only)
    with pytest.raises(RuntimeError, match="mismatch"):
        fixture.owned_state()


def test_start_never_overwrites_existing_handoff(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    path.write_text("retained", encoding="utf-8")
    monkeypatch.setattr(fixture, "STATE", path)
    with pytest.raises(RuntimeError, match="already exists"):
        fixture.start()
    assert path.read_text(encoding="utf-8") == "retained"
