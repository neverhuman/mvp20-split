"""Independent Studio closure must include new groups and exact validation pins."""
import json
from pathlib import Path

import pytest

from verify_studio import public_schemas


def publish(root, group, entries, profiles=None):
    directory = root / "src/contracts/generated" / group
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.json").write_text(json.dumps(entries), encoding="utf-8")
    if profiles is not None:
        (directory / "profiles.json").write_text(json.dumps(profiles), encoding="utf-8")


def test_new_public_groups_and_validation_profiles_are_not_omitted(tmp_path):
    publish(tmp_path, "", {"snapshot": {"source": "contracts/schemas/v1/snapshot.serialization.json", "sha256": "original"}})
    for group in ("launch", "successor_launch", "campaign_origin", "campaign_curation", "search"):
        publish(tmp_path, group, {"request": {"source": f"contracts/schemas/v1/{group}.serialization.json", "sha256": group}},
                {"request": {"sha256": "validation-" + group}})
    result = public_schemas(tmp_path)
    assert len(result) == 11
    assert result["snapshot"]["sha256"] == "original"
    for group in ("launch", "successor_launch", "campaign_origin", "campaign_curation", "search"):
        assert result[group + ".validation.request"] == {
            "source": f"contracts/schemas/v1/{group}.validation.json", "sha256": "validation-" + group}


def test_missing_profile_source_fails_closed(tmp_path):
    publish(tmp_path, "new", {}, {"missing": {"sha256": "pin"}})
    with pytest.raises(KeyError):
        public_schemas(tmp_path)


def test_missing_manifests_do_not_qualify_an_empty_consumer(tmp_path):
    with pytest.raises(AssertionError, match="No published"):
        public_schemas(tmp_path)


def test_nonserialization_profile_cannot_guess_a_validation_path(tmp_path):
    publish(tmp_path, "new", {"item": {"source": "elsewhere.json", "sha256": "pin"}}, {"item": {"sha256": "other"}})
    with pytest.raises(AssertionError):
        public_schemas(tmp_path)
