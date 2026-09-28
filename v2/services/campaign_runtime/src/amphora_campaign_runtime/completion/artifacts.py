"""Configured authenticated artifact reservation transport, outside runtime SQL."""

import json
import uuid
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from amphora_contracts_artifacts import ReservationReceipt, parse_command


class ReservationUnavailable(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ArtifactReservations:
    def __init__(self, owner, endpoint, token, *, timeout=5):
        url = urlsplit(endpoint)
        if (url.username or url.password or url.query or url.fragment or not url.hostname
            or (url.scheme != "https" and not (url.scheme == "http" and url.hostname in {"127.0.0.1", "::1"}))
            or not owner or len(token) < 32 or not 0 < timeout <= 30):
            raise ValueError("Invalid artifact endpoint configuration")
        self.owner, self.endpoint, self.token, self.timeout = owner, endpoint, token, timeout
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def reserve(self, reservation):
        if reservation.intent.runtime_owner != self.owner:
            raise ReservationUnavailable("runtime_owner_mismatch")
        # Stable across restart/retry; neither attempt number nor transport timing alters identity.
        identity = uuid.uuid5(uuid.NAMESPACE_URL, json.dumps(reservation.model_dump(mode="json"),
            sort_keys=True, separators=(",", ":"))).hex
        command = parse_command("artifacts.reserve", json.dumps({"identity": {
            "command_family": "artifacts.reserve", "command_id": identity, "actor_id": self.owner,
            "scope": reservation.artifact.scope.model_dump()}, "payload": reservation.model_dump(mode="json")}))
        request = Request(self.endpoint, data=command.canonical_bytes, method="POST", headers={
            "Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                raw = response.read(262145)
                if len(raw) > 262144:
                    raise ReservationUnavailable("artifact_response_too_large")
                receipt = ReservationReceipt.model_validate_json(raw)
        except (URLError, OSError, ValueError) as error:
            raise ReservationUnavailable("artifact_reservation_unavailable") from error
        validate_receipt(reservation, receipt)
        return receipt


def validate_receipt(reservation, receipt):
    binding = receipt.outcome.binding
    if (receipt.outcome.status != "reserved" or binding.artifact != reservation.artifact
        or binding.intent != reservation.intent):
        raise ReservationUnavailable("artifact_reservation_binding_mismatch")
