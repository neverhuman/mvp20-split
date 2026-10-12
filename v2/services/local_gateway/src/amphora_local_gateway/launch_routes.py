"""Closed method/path policy for fresh and additive successor launches."""
import re
from dataclasses import dataclass
from urllib.parse import unquote, urlsplit
from .configuration import require


@dataclass(frozen=True)
class LaunchRoute:
    method: str

    @classmethod
    def parse(cls, target):
        parsed = urlsplit(target); parts = parsed.path.split('/')
        method = None
        if parts == ['', 'v1', 'campaign-launch-profiles']:
            method = 'GET'
        elif len(parts) >= 3 and parts[2] in {'campaign-launches','campaign-successor-launches'}:
            if len(parts) == 3:
                method = 'POST'
            elif len(parts) == 4 and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',unquote(parts[3])):
                method = 'GET'
            elif parts == ['', 'v1', 'campaign-successor-launches', 'receipts', 'query']:
                method = 'POST'
        require(method is not None and not parsed.query, 'gateway_launch_route')
        return cls(method)

    def check(self, method, body):
        require(method == self.method and len(body) <= 262144 and (method != 'GET' or not body),
            'gateway_launch_request_bound')
