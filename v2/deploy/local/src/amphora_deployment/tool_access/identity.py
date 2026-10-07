"""Create-once local server identity; encrypted PEM and current-user protected password."""

import hashlib
import json
import os
import secrets
import ssl
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..credentials import CredentialVault, SecretBundle
from ..profile import fields, label, require

HOSTNAME = "host.docker.internal"


def digest(path, maximum):
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(0 < len(raw) <= maximum, "tool_tls_file_size")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TLSIdentity:
    directory: Path
    deployment_id: str
    certificate_sha256: str
    encrypted_key_sha256: str

    @property
    def certificate(self):
        return self.directory / "certificate.pem"

    @property
    def vault(self):
        return CredentialVault(
            self.directory / "password.dpapi", self.deployment_id + "-tool-tls"
        )

    @classmethod
    def create(cls, directory, deployment_id, openssl):
        deployment_id = label(deployment_id, "tool_tls_deployment")
        directory, openssl = Path(directory).absolute(), Path(openssl).absolute()
        require(openssl.is_file(), "tool_tls_openssl_missing")
        executable_sha = digest(openssl, 33554432)
        directory.mkdir(parents=True, exist_ok=False)
        password = secrets.token_urlsafe(48)
        vault = CredentialVault(
            directory / "password.dpapi", deployment_id + "-tool-tls"
        )
        vault.create(SecretBundle({"TLS_KEY_PASSWORD": password}))
        configuration = directory / "request.cnf"
        configuration.write_text(
            "[req]\ndistinguished_name=subject\n[subject]\n", encoding="ascii"
        )
        environment = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC"}
        }
        environment["AMPHORA_TLS_KEY_PASSWORD"] = password
        command = [
            str(openssl),
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-sha256",
            "-days",
            "30",
            "-config",
            str(configuration),
            "-keyout",
            str(directory / "encrypted-key.pem"),
            "-out",
            str(directory / "certificate.pem"),
            "-passout",
            "env:AMPHORA_TLS_KEY_PASSWORD",
            "-subj",
            "/CN=" + HOSTNAME,
            "-addext",
            "subjectAltName=DNS:" + HOSTNAME,
            "-addext",
            "basicConstraints=critical,CA:FALSE",
            "-addext",
            "keyUsage=critical,digitalSignature,keyEncipherment",
            "-addext",
            "extendedKeyUsage=serverAuth",
        ]
        result = subprocess.run(
            command,
            env=environment,
            capture_output=True,
            timeout=30,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        require(result.returncode == 0, "tool_tls_generation_failed")
        require(
            b"BEGIN ENCRYPTED PRIVATE KEY"
            in (directory / "encrypted-key.pem").read_bytes(),
            "tool_tls_key_protection",
        )
        record = {
            "profile": "local-tool-tls-identity.v1",
            "deployment_id": deployment_id,
            "hostname": HOSTNAME,
            "certificate_sha256": digest(directory / "certificate.pem", 16384),
            "encrypted_key_sha256": digest(directory / "encrypted-key.pem", 16384),
            "openssl_sha256": executable_sha,
        }
        with (directory / "identity.json").open("x", encoding="utf-8") as stream:
            json.dump(record, stream, sort_keys=True, separators=(",", ":"))
            stream.flush()
            os.fsync(stream.fileno())
        selected = cls.load(directory)
        selected.server_context()  # Actual certificate/key/password compatibility before acceptance.
        return selected

    @classmethod
    def load(cls, directory):
        directory = Path(directory).absolute()
        with (directory / "identity.json").open("rb") as stream:
            raw = stream.read(8193)
        require(len(raw) <= 8192, "tool_tls_manifest_size")
        value = fields(
            json.loads(raw),
            "profile deployment_id hostname certificate_sha256 encrypted_key_sha256 openssl_sha256",
            "tool_tls_identity",
        )
        require(
            value["profile"] == "local-tool-tls-identity.v1"
            and value["hostname"] == HOSTNAME,
            "tool_tls_profile",
        )
        deployment_id = label(value["deployment_id"], "tool_tls_deployment")
        require(
            digest(directory / "certificate.pem", 16384) == value["certificate_sha256"]
            and digest(directory / "encrypted-key.pem", 16384)
            == value["encrypted_key_sha256"],
            "tool_tls_identity_digest",
        )
        return cls(
            directory,
            deployment_id,
            value["certificate_sha256"],
            value["encrypted_key_sha256"],
        )

    def server_context(self):
        require(self == self.load(self.directory), "tool_tls_identity_binding")
        password = self.vault.load().environment(["TLS_KEY_PASSWORD"])[
            "TLS_KEY_PASSWORD"
        ]
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(
            self.certificate, self.directory / "encrypted-key.pem", password=password
        )
        return context
