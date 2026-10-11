"""Fixed loopback owner forwarding with bounded bytes and no redirects."""

from dataclasses import dataclass
import http.client
import json
import re
from urllib.parse import parse_qsl, unquote, urlsplit

from .configuration import require, GatewayError


ALIASES = {"runtime":"runtime", "artifacts":"artifact", "data":"artifact", "registry":"registry",
           "knowledge":"knowledge", "research":"research", "planning":"planning", "deployment":"deployment"}
MAXIMUM_BODY = 1048576
MAXIMUM_RESPONSE = 8388608


@dataclass(frozen=True)
class Route:
    owner: str
    target: str

    @property
    def campaign_origin(self):
        return self.owner == 'planning' and self.target.startswith('/v1/campaign-origins')

    @classmethod
    def parse(cls, path):
        require(type(path) is str and len(path) <= 16384 and path.isascii() and not any(ord(c) < 32 for c in path), "gateway_route")
        parsed = urlsplit(path)
        parts = parsed.path.split("/")
        require(not parsed.scheme and not parsed.netloc and not parsed.fragment and len(parts) >= 5 and
                parts[:2] == ["", "api"] and parts[2] in ALIASES and parts[3] == "v1", "gateway_route")
        decoded = unquote(parsed.path)
        require("%2f" not in parsed.path.lower() and "\\" not in decoded and not any(part in (".", "..", "") for part in decoded.split("/")[1:]) and
                "%" not in decoded and all(ord(c) >= 32 for c in decoded), "gateway_route_encoding")
        target = "/" + "/".join(parts[3:]) + ("?" + parsed.query if parsed.query else "")
        if parts[2] == 'planning' and parts[4].startswith('campaign-origins'):
            pairs = parse_qsl(parsed.query, keep_blank_values=True)
            query = dict(pairs)
            require(parts[4] == 'campaign-origins' and len(parts) == 6 and
                    bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', unquote(parts[5]))) and
                    len(pairs) == 2 and set(query) == {'revision', 'content_sha256'} and
                    bool(re.fullmatch(r'[1-9][0-9]{0,15}', query['revision'])) and
                    int(query['revision']) <= 9007199254740991 and
                    bool(re.fullmatch(r'[0-9a-f]{64}', query['content_sha256'])), 'gateway_campaign_origin_route')
        if parts[2] == 'deployment':
            allowed = (len(parts) == 5 and parts[4] in {'campaign-launches', 'campaign-launch-profiles'}
                or len(parts) == 6 and parts[4] == 'campaign-launches'
                and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', unquote(parts[5])))
            require(bool(allowed) and not parsed.query, 'gateway_launch_route')
        return cls(ALIASES[parts[2]], target)


def forward(peer, route, method, body, request_id):
    require(method in {"GET", "POST"} and len(body) <= MAXIMUM_BODY, "gateway_request_bound")
    if route.campaign_origin:
        require(method == 'GET' and not body, 'gateway_campaign_origin_read_only')
    maximum_response = 262144 if route.campaign_origin else MAXIMUM_RESPONSE
    if route.owner == 'deployment':
        require(len(body) <= 262144 and (method == 'GET' or route.target == '/v1/campaign-launches'), 'gateway_launch_request_bound')
    connection = http.client.HTTPConnection("127.0.0.1", peer.port, timeout=15)
    try:
        headers = {"Authorization":"Bearer " + peer.token, "Accept":"application/json, application/octet-stream",
                   "X-Amphora-Request-Id":request_id}
        if body:
            headers["Content-Type"] = "application/json"
        connection.request(method, route.target, body=body or None, headers=headers)
        response = connection.getresponse()
        require(not 300 <= response.status < 400, "gateway_owner_redirect")
        if response.status >= 400:
            if route.owner == 'deployment' or route.campaign_origin:
                raw = response.read(4097)
                try:
                    error = json.loads(raw) if len(raw) <= 4096 else None
                except ValueError:
                    error = None
                allowed = {'launch_slot_busy', 'launch_request_conflict', 'launch_scope_denied',
                    'launch_profile_mismatch', 'launch_profile_limit', 'launch_request_invalid',
                    'launch_unavailable', 'launch_receipt_unavailable'}
                if route.campaign_origin:
                    allowed = {'campaign_origin_not_recorded', 'campaign_origin_inconsistent',
                        'campaign_origin_response_limit', 'invalid_campaign_origin_request', 'planning_access_denied'}
                if type(error) is dict and type(error.get('reason_code')) is str and error['reason_code'] in allowed:
                    return response.status, 'application/json', json.dumps({'reason_code': error['reason_code']}).encode()
            # Preserve the status used by Studio, never expose private owner diagnostics.
            return response.status, "application/json", b'{"error":"owner_request_rejected"}'
        size = response.getheader("Content-Length")
        require(size is None or size.isdecimal() and int(size) <= maximum_response, "gateway_response_bound")
        raw = response.read(maximum_response + 1)
        require(len(raw) <= maximum_response, "gateway_response_bound")
        if size is not None:
            require(len(raw) == int(size), "gateway_response_truncated")
        content_type = response.getheader("Content-Type", "application/octet-stream")
        require(len(content_type) <= 128 and all(32 <= ord(c) <= 126 for c in content_type), "gateway_content_type")
        # Arbitrary retained bytes must not become executable content on Studio's origin.
        if content_type.split(";")[0].strip().lower() not in {
            "application/json", "application/octet-stream", "text/plain", "image/png", "image/jpeg", "image/webp"
        }:
            content_type = "application/octet-stream"
        return response.status, content_type, raw
    except (OSError, http.client.HTTPException):
        raise GatewayError("gateway_owner_unavailable") from None
    finally:
        connection.close()
