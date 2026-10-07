"""Actual encrypted key, current-user protection and TLS trust/hostname verification."""

import os
import socket
import ssl
import threading
from pathlib import Path

import pytest
from amphora_deployment import ProfileError
from amphora_deployment.tool_access import TLSIdentity
from amphora_deployment.tool_access.identity import HOSTNAME

OPENSSL = Path("C:/Program Files/Git/usr/bin/openssl.exe")
pytestmark = pytest.mark.skipif(
    os.name != "nt" or not OPENSSL.is_file(), reason="Selected Windows/OpenSSL profile"
)


def exchange(identity, *, trust=True, hostname=HOSTNAME):
    server = identity.server_context()
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener.settimeout(5)
    port = listener.getsockname()[1]

    def serve():
        try:
            connection, _ = listener.accept()
            with connection:
                connection.settimeout(5)
                try:
                    with server.wrap_socket(connection, server_side=True) as secured:
                        secured.sendall(b"local-tool-tls")
                except (ssl.SSLError, ConnectionResetError):
                    if trust and hostname == HOSTNAME:
                        raise
                    # Windows may reset instead of sending an SSL alert after client rejection.
        finally:
            listener.close()

    thread = threading.Thread(target=serve)
    thread.start()
    try:
        client = ssl.create_default_context(
            cafile=str(identity.certificate) if trust else None
        )
        with (
            socket.create_connection(("127.0.0.1", port), timeout=5) as connection,
            client.wrap_socket(connection, server_hostname=hostname) as secured,
        ):
            return secured.recv(128)
    finally:
        thread.join(6)
        assert not thread.is_alive()


def test_actual_trust_and_wrong_hostname_or_untrusted_rejection(identity):
    assert exchange(identity) == b"local-tool-tls"
    with pytest.raises(ssl.SSLCertVerificationError):
        exchange(identity, hostname="localhost")
    with pytest.raises(ssl.SSLCertVerificationError):
        exchange(identity, trust=False)


def test_create_once_protects_private_key_and_preserves_identity(identity):
    assert (
        b"BEGIN ENCRYPTED PRIVATE KEY"
        in (identity.directory / "encrypted-key.pem").read_bytes()
    )
    assert b"PRIVATE KEY" not in identity.certificate.read_bytes()
    password = identity.vault.load().environment(["TLS_KEY_PASSWORD"])[
        "TLS_KEY_PASSWORD"
    ]
    for filename in ("identity.json", "encrypted-key.pem", "password.dpapi"):
        assert password.encode() not in (identity.directory / filename).read_bytes()
    assert TLSIdentity.load(identity.directory) == identity
    with pytest.raises(FileExistsError):
        TLSIdentity.create(identity.directory, identity.deployment_id, OPENSSL)
    assert TLSIdentity.load(identity.directory) == identity


def test_modified_key_or_certificate_fails_before_tls_setup(identity):
    identity.certificate.write_bytes(identity.certificate.read_bytes() + b"\n")
    with pytest.raises(ProfileError, match="tool_tls_identity_digest"):
        identity.server_context()
