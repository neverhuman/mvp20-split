import hashlib
import os
import subprocess
import uuid

import pytest
from amphora_contracts_artifacts import ContentDescriptor
from amphora_data_artifacts.publication.model import UploadAttempt, UploadError
from amphora_data_artifacts.storage.local import LocalBytes


def attempt(key=None):
    content = ContentDescriptor.model_validate_json('{"sha256":"' + hashlib.sha256(b"abc").hexdigest() +
        '","size_bytes":3,"media_type":"application/octet-stream","schema_ref":'
        '{"schema_id":"fixture.bytes","version":"1","sha256":"' + "a" * 64 + '"}}')
    return UploadAttempt("upload", "attempt", 1, key or uuid.uuid4().hex, content)


@pytest.mark.parametrize("key", ["../escape", "/absolute", "A" * 32, "a/b", "a" * 31])
def test_paths_reject_non_generated_keys(tmp_path, key):
    with pytest.raises(UploadError, match="invalid_storage_key"):
        LocalBytes(tmp_path).writer(attempt(key))


def test_exclusive_write_and_bounded_content(tmp_path):
    store = LocalBytes(tmp_path)
    item = attempt()
    writer = store.writer(item)
    writer.write(b"ab")
    with pytest.raises(UploadError, match="content_size_mismatch"):
        writer.write(b"cd")
    writer.write(b"c")
    writer.seal()
    writer.close()
    assert store.path(item.storage_key).read_bytes() == b"abc"
    with pytest.raises(FileExistsError):
        store.writer(item)


def test_symlink_root_or_entry_denied(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(real, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(real)], check=True, capture_output=True)
    with pytest.raises(UploadError, match="unsafe_storage_path"):
        LocalBytes(link)
    store = LocalBytes(real)
    item = attempt()
    entry = real / item.storage_key
    try:
        entry.symlink_to(tmp_path / "outside")
    except OSError:
        subprocess.run(["cmd", "/c", "mklink", "/J", str(entry), str(tmp_path)], check=True, capture_output=True)
    with pytest.raises(UploadError, match="unsafe_storage_path"):
        store.writer(item)
