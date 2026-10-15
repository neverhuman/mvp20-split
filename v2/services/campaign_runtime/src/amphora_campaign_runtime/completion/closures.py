"""Explicit derived-closure transport; never substitutes ordinary reservations."""

import json
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request

from amphora_contracts_artifact_retention import (
    DerivedClosureReservationReceipt, ReserveDerivedClosure, parse_derived_closure_command,
)

from .artifacts import ArtifactReservations, ReservationUnavailable, validate_receipt


PROFILE = "derived-closure-retention-v1"


class ClosureReservations(ArtifactReservations):
    def __init__(self, owner, endpoint, token, *, timeout=5):
        super().__init__(owner, endpoint, token, timeout=timeout)
        if urlsplit(endpoint).path != "/v1/retention-closures/reserve":
            raise ValueError("Invalid closure endpoint configuration")

    def require_available(self):
        """Read-only route/schema qualification, before opening owner transactions."""
        url = urlsplit(self.endpoint)
        origin = urlunsplit((url.scheme, url.netloc, "", "", ""))
        try:
            with self.opener.open(Request(origin + "/ready"), timeout=self.timeout) as response:
                if response.status != 200 or json.loads(response.read(4097)) != {"ready": True}:
                    raise ReservationUnavailable("artifact_closure_unavailable")
            request = Request(origin + "/v1/retention-closures/" + uuid.uuid4().hex,
                              headers={"Authorization": "Bearer " + self.token})
            try:
                with self.opener.open(request, timeout=self.timeout):
                    raise ReservationUnavailable("artifact_closure_unavailable")
            except HTTPError as response:
                with response:
                    if response.code != 404 or json.loads(response.read(4097)) != {"reason_code": "reservation_unavailable"}:
                        raise ReservationUnavailable("artifact_closure_unavailable")
        except (URLError, OSError, ValueError) as error:
            raise ReservationUnavailable("artifact_closure_unavailable") from error

    def reserve(self, reservation):
        if reservation.intent.runtime_owner != self.owner:
            raise ReservationUnavailable("runtime_owner_mismatch")
        payload = ReserveDerivedClosure(**reservation.model_dump(), profile=PROFILE)
        identity = uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(payload.model_dump(mode="json"),
            sort_keys=True, separators=(",", ":"))).hex
        command = parse_derived_closure_command(json.dumps({"identity": {
            "command_family": "artifacts.reserve_derived_closure", "command_id": identity,
            "actor_id": self.owner, "scope": reservation.artifact.scope.model_dump()},
            "payload": payload.model_dump(mode="json")}))
        request = Request(self.endpoint, data=command.canonical_bytes, method="POST", headers={
            "Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise ReservationUnavailable("artifact_closure_unavailable")
                raw = response.read(262145)
                if len(raw) > 262144:
                    raise ReservationUnavailable("artifact_response_too_large")
                receipt = DerivedClosureReservationReceipt.model_validate_json(raw)
        except (URLError, OSError, ValueError) as error:
            raise ReservationUnavailable("artifact_closure_unavailable") from error
        validate_receipt(reservation, receipt.reservation)
        return receipt
