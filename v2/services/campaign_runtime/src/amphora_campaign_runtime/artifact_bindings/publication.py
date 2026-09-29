"""Receipt-first Artifact publication through public HTTP only."""

import hashlib
import json
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from amphora_contracts_artifacts import (
    FinalizedReceipt,
    PublicationObservation,
    UploadContentReceipt,
    UploadReceipt,
    parse_command,
)

from ..coordinator.projections import ArtifactProjections, NoRedirect, ProjectionUnavailable
from ..coordinator.values import ensure


class ArtifactPublisher:
    def __init__(self, endpoint, token, owner):
        self.reader = ArtifactProjections(endpoint, token)
        self.owner = owner

    def request(self, method, path, body=None):
        request = Request(self.reader.endpoint + path, data=body, method=method,
            headers={"Authorization": "Bearer " + self.reader.token, "Content-Type": "application/json"})
        try:
            with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=10) as response:
                result = response.read(262145)
                ensure(len(result) <= 262144, "binding_peer_response_size")
                return response.status, result
        except HTTPError as error:
            return error.code, error.read(262145)
        except (URLError, OSError, TimeoutError) as error:
            raise ProjectionUnavailable("binding_publication_unavailable") from error

    def command(self, address, slot, family, data):
        return parse_command(family, json.dumps({"identity": {"scope": address.scope.model_dump(mode="json"),
            "actor_id": self.owner, "command_family": family, "command_id": address.operation(family, slot)}, "payload": data}))

    @staticmethod
    def decoded(model, raw):
        try:
            return model.model_validate_json(raw)
        except ValueError as error:
            raise ProjectionUnavailable("binding_publication_response_invalid") from error

    def observe(self, command):
        status, body = self.request("GET", "/v1/commands/" + command.identity.command_family + "/" + command.identity.command_id)
        if status == 404:
            return None
        if status != 200:
            raise ProjectionUnavailable("binding_publication_history_unavailable")
        try:
            result = PublicationObservation.model_validate_json(body)
        except ValueError as error:
            raise ProjectionUnavailable("binding_publication_history_invalid") from error
        ensure(result.identity == command.identity and result.request_sha256 == command.sha256, "binding_publication_identity")
        ensure(result.outcome.status != "rejected", "binding_publication_rejected")
        return result.outcome

    def publish(self, address, slot, body, schema, guard):
        content = {"sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body),
                   "media_type": "application/json", "schema_ref": schema.model_dump(mode="json")}
        begin = self.command(address, slot, "artifacts.begin_upload", {"content": content})
        guard()
        status, raw = self.request("POST", "/v1/uploads", begin.canonical_bytes)
        if status != 200:
            self.observe(begin)
            raise ProjectionUnavailable("binding_upload_unavailable")
        upload = self.decoded(UploadReceipt, raw)
        ensure(upload.scope == address.scope and upload.content.model_dump(mode="json") == content, "binding_upload_mismatch")
        finalize = self.command(address, slot, "artifacts.finalize", {"upload_id": upload.upload_id, "content": content})
        guard()
        previous = self.observe(finalize)
        ensure(previous is None or previous.status in {"pending", "finalized"}, "binding_publication_outcome_mismatch")
        if previous is not None and previous.status == "finalized":
            result = previous.receipt
        else:
            if previous is None:
                guard()
                status, raw = self.request("PUT", "/v1/uploads/" + upload.upload_id + "/content", body)
                if status != 200:
                    raise ProjectionUnavailable("binding_stream_unavailable")
                ensure(self.decoded(UploadContentReceipt, raw).upload_id == upload.upload_id, "binding_stream_mismatch")
            guard()
            status, raw = self.request("POST", "/v1/artifacts/finalize", finalize.canonical_bytes)
            if status != 200:
                self.observe(finalize)
                raise ProjectionUnavailable("binding_finalize_unavailable")
            result = self.decoded(FinalizedReceipt, raw)
        reference = result.artifact
        ensure(result.upload_id == upload.upload_id and reference.scope == address.scope and all(
            reference.model_dump(mode="json")[key] == value for key, value in content.items()), "binding_finalization_mismatch")
        return reference
