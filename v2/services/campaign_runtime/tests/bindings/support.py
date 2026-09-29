"""Explicit scripted Artifact peer; database tests do not claim installed-peer proof."""

import hashlib
import json
from decimal import Decimal

from amphora_campaign_runtime.artifact_bindings.encoding import payload
from amphora_contracts_artifacts import ReservationReceipt
from amphora_contracts_core import ArtifactRef


class MemoryArtifacts:
    owner = "binding-runtime"

    def __init__(self, scope):
        self.scope, self.documents, self.reservations = scope, {}, {}
        self.reader = self
        self.on_reserve = None

    def put(self, data, schema):
        return self.store(payload(data), schema)

    def store(self, body, schema):
        digest = hashlib.sha256(body).hexdigest()
        reference = ArtifactRef.model_validate({"scope": self.scope, "artifact_id": digest,
            "sha256": digest, "size_bytes": len(body), "schema_ref": schema, "media_type": "application/json"})
        self.documents[reference.artifact_id] = body
        return reference

    def fetch(self, reference):
        body = self.documents[reference.artifact_id]
        assert len(body) == reference.size_bytes and hashlib.sha256(body).hexdigest() == reference.sha256
        return json.loads(body, parse_float=Decimal)

    def publish(self, address, slot, body, schema, guard):
        guard()
        return self.store(body, schema)

    def reserve(self, request):
        key = request.intent.output_binding
        if self.on_reserve:
            callback, self.on_reserve = self.on_reserve, None
            callback(request)
        self.reservations[key] = request
        return ReservationReceipt.model_validate({"outcome": {"status": "reserved", "binding": {
            "reservation_id": hashlib.sha256(request.model_dump_json().encode()).hexdigest(),
            "artifact": request.artifact, "intent": request.intent}}})
