"""Public Data reads with distinct denied, unavailable and invalid-reference outcomes."""

import hashlib
import http.client
import json
import socket
import threading
import time
from urllib.parse import urlsplit

from amphora_contracts_artifacts import DerivationReceipt
from amphora_contracts_core import ArtifactRef, Scope

from .policy import AssessmentError


class AssessmentPeerUnavailable(AssessmentError):
    """Retry the same assessment; unavailable evidence is not a negative finding."""


def _decode(model, content):
    def unique(pairs):
        values = {}
        for key, value in pairs:
            if key in values:
                raise ValueError("duplicate_key")
            values[key] = value
        return values

    def constant(_):
        raise ValueError("nonfinite")

    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=unique, parse_constant=constant)
        return model.model_validate_json(json.dumps(value, allow_nan=False))
    except (ValueError, RecursionError) as error:
        raise AssessmentPeerUnavailable("peer_protocol_error") from error


class AssessmentDataReader:
    """One resolution attempt, one scope and one finite read budget; no cross-request cache."""

    def __init__(self, endpoint: str, token: str, scope: Scope):
        try:
            parsed = urlsplit(endpoint)
            valid = (parsed.scheme == "http" and parsed.hostname == "127.0.0.1"
                     and parsed.port is not None and 1 <= parsed.port <= 65535
                     and parsed.username is None and parsed.password is None
                     and parsed.path in ("", "/") and not parsed.query and not parsed.fragment)
        except (ValueError, TypeError, AttributeError):
            valid = False
        if not valid:
            raise AssessmentError("explicit_loopback_peer_required")
        if (not isinstance(token, str) or not 32 <= len(token) <= 512
                or any(not 33 <= ord(char) <= 126 for char in token)):
            raise AssessmentError("invalid_peer_credential")
        self._port, self._token, self.scope = parsed.port, token, scope
        self._deadline = time.monotonic() + 30
        self._calls = 0
        self._bytes = 0
        self._references = {}
        self._contents = {}
        self._derivations = {}

    @property
    def consumed(self) -> tuple[ArtifactRef, ...]:
        return tuple(self._references[key] for key in sorted(self._contents))

    def _remaining(self):
        remaining = self._deadline - time.monotonic()
        if remaining <= 0:
            raise AssessmentPeerUnavailable("peer_deadline")
        return min(5, remaining)

    def _admit(self, reference):
        self._remaining()
        if reference.scope != self.scope:
            raise AssessmentError("artifact_scope_mismatch")
        previous = self._references.get(reference.artifact_id)
        if previous is not None and previous != reference:
            raise AssessmentError("artifact_identity_conflict")
        if previous is None and len(self._references) >= 128:
            raise AssessmentError("assessment_input_limit")
        if reference.size_bytes > 16 * 1024 * 1024:
            raise AssessmentError("artifact_read_limit")
        self._references[reference.artifact_id] = reference

    def _get(self, path, limit):
        self._remaining()
        if self._calls >= 384:
            raise AssessmentError("peer_call_limit")
        self._calls += 1
        connection = http.client.HTTPConnection("127.0.0.1", self._port, timeout=self._remaining())
        timer = None
        try:
            connection.connect()
            active = connection.sock

            def expire():
                try:
                    active.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass

            timer = threading.Timer(max(0, self._deadline - time.monotonic()), expire)
            timer.daemon = True
            timer.start()
            connection.request("GET", path, headers={"Authorization": "Bearer " + self._token})
            active.settimeout(self._remaining())
            response = connection.getresponse()
            if response.status in (401, 403):
                raise AssessmentError("peer_access_denied")
            if response.status == 404:
                raise AssessmentError("reference_unavailable")
            if response.status != 200:
                raise AssessmentPeerUnavailable("peer_unavailable")
            blocks, size = [], 0
            while True:
                active.settimeout(self._remaining())
                block = response.read1(min(65536, limit + 1 - size))
                self._remaining()
                size += len(block)
                self._bytes += len(block)
                if size > limit or self._bytes > 32 * 1024 * 1024:
                    raise AssessmentError("peer_response_limit")
                blocks.append(block)
                if not block or response.isclosed():
                    return b"".join(blocks)
        except (OSError, http.client.HTTPException) as error:
            self._remaining()
            raise AssessmentPeerUnavailable("peer_unavailable") from error
        finally:
            if timer is not None:
                timer.cancel()
            connection.close()

    def read(self, reference: ArtifactRef) -> bytes:
        self._admit(reference)
        key = reference.artifact_id
        if key not in self._contents:
            path = f"/v1/artifacts/{key}"
            if _decode(ArtifactRef, self._get(path, 262144)) != reference:
                raise AssessmentError("artifact_reference_mismatch")
            content = self._get(path + "/content", reference.size_bytes)
            if len(content) != reference.size_bytes or hashlib.sha256(content).hexdigest() != reference.sha256:
                raise AssessmentError("artifact_integrity_mismatch")
            self._contents[key] = content
        return self._contents[key]

    def published(self, reference: ArtifactRef, publishers: frozenset[str]) -> tuple[bytes, DerivationReceipt]:
        # Rights-authorized content must be read even when historical lineage is readable.
        content = self.read(reference)
        key = reference.artifact_id
        if key not in self._derivations:
            proof = _decode(DerivationReceipt, self._get(f"/v1/artifacts/{key}/derivation", 262144))
            if (proof.artifact != reference or proof.origin.scope != self.scope
                    or proof.origin.command_family != "artifacts.begin_derived_upload"
                    or any(item.scope != self.scope for item in proof.declaration.inputs)):
                raise AssessmentError("derivation_reference_mismatch")
            self._derivations[key] = proof
        proof = self._derivations[key]
        if proof.origin.actor_id not in publishers:
            raise AssessmentError("untrusted_publisher")
        return content, proof
