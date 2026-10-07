"""Actual current-user DPAPI, fresh-process recovery and minimal environment grants."""

import hashlib
import os
import subprocess
import sys

import pytest

from amphora_deployment import ProfileError
from amphora_deployment.credentials import CredentialVault, SecretBundle
from amphora_deployment.credentials.protection import transform


pytestmark = pytest.mark.skipif(os.name != "nt", reason="Actual selected Windows user protection required")


def test_actual_protection_and_fresh_process_recovery(tmp_path):
    secret = "synthetic-vault-secret-only-for-testing"
    bundle = SecretBundle({"DB_PASSWORD": secret, "SERVICE_TOKEN": "second-test-value"})
    vault = CredentialVault(tmp_path / "credentials.dpapi", "test-deployment")
    vault.create(bundle)
    assert secret.encode() not in vault.path.read_bytes()
    assert secret not in repr(bundle)
    assert vault.load().names == ("DB_PASSWORD", "SERVICE_TOKEN")
    assert vault.load().environment(["DB_PASSWORD"]) == {"DB_PASSWORD": secret}
    script = "import hashlib,sys; from amphora_deployment.credentials import CredentialVault; "
    script += "v=CredentialVault(sys.argv[1],'test-deployment').load().environment(['DB_PASSWORD'])['DB_PASSWORD']; "
    script += "assert hashlib.sha256(v.encode()).hexdigest()==sys.argv[2]"
    result = subprocess.run([sys.executable, "-I", "-c", script, str(vault.path), hashlib.sha256(secret.encode()).hexdigest()],
                            capture_output=True, timeout=15)
    assert result.returncode == 0 and secret.encode() not in result.stdout + result.stderr
    before = vault.path.read_bytes()
    with pytest.raises(FileExistsError):
        vault.create(SecretBundle({"DB_PASSWORD": "replacement"}))
    assert vault.path.read_bytes() == before


def test_wrong_deployment_and_malformed_ciphertext_fail_closed(tmp_path):
    path = tmp_path / "vault.dpapi"
    CredentialVault(path, "first").create(SecretBundle({"TOKEN": "test-only"}))
    with pytest.raises(ProfileError, match="credential_protection_failed"):
        CredentialVault(path, "other").load()
    path.write_bytes(b"not-a-protected-blob")
    with pytest.raises(ProfileError, match="credential_protection_failed"):
        CredentialVault(path, "first").load()


def test_bounded_input_and_missing_grant():
    with pytest.raises(ProfileError, match="credential_blob_bound"):
        transform(b"x" * 65537, b"context", protect=True)
    with pytest.raises(ProfileError, match="credential_context_bound"):
        transform(b"value", b"", protect=True)
    with pytest.raises(ProfileError, match="credential_reference_missing"):
        SecretBundle({"TOKEN": "value"}).environment(["MIGRATOR"])
    for values in ({}, {"bad-name": "secret"}, {"TOKEN": ""}, {"TOKEN": "\x00"}):
        with pytest.raises(ProfileError):
            SecretBundle(values)
