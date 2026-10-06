"""One direct TLS request, no redirects/retries/proxies or remote tool execution."""
import hashlib
import http.client
import json
import time

from ..context.policy import require
from ..providers.port import ProviderUnavailable

MAX_ENVELOPE = 1048576

class OpenAIHTTP:
    def __init__(self, api_key, *, timeout_seconds=45, connection_factory=http.client.HTTPSConnection):
        require(type(api_key) is str and bool(api_key) and "\n" not in api_key and "\r" not in api_key, "openai_credentials_missing")
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 60, "openai_timeout")
        self._key,self.timeout,self.factory = api_key,timeout_seconds,connection_factory
        self.last_failure = None
    def send(self, body):
        require(type(body) is bytes and 0 < len(body) <= 16384, "openai_http_body")
        self.last_failure = None
        deadline=time.monotonic()+self.timeout
        connection=self.factory("api.openai.com",timeout=self.timeout)
        try:
            connection.request("POST","/v1/responses",body=body,headers={"Authorization":"Bearer "+self._key,"Content-Type":"application/json","Accept":"application/json"})
            remaining=deadline-time.monotonic()
            if remaining <= 0: raise TimeoutError("openai_deadline")
            if connection.sock is not None: connection.sock.settimeout(remaining)
            response=connection.getresponse()
            if response.status != 200:
                self.last_failure = {"http_status": response.status,
                    "request_body_sha256": hashlib.sha256(body).hexdigest(), "code": "unclassified", "parameter": None}
                # Read a bounded error envelope; only closed enum values may leave here.
                # Never retain/log the free-form message or any arbitrary error field.
                try:
                    error = json.loads(response.read1(8192)).get("error", {})
                    code, parameter = error.get("code"), error.get("param")
                    if code in {"insufficient_quota", "invalid_api_key", "rate_limit_exceeded", "model_not_found", "unsupported_parameter", "unsupported_value", "invalid_request_error"}:
                        self.last_failure["code"] = code
                    if parameter in {"model", "reasoning", "reasoning.effort", "max_output_tokens", "text.format", "service_tier", "store", "input", "instructions"}:
                        self.last_failure["parameter"] = parameter
                except (ValueError, AttributeError, TypeError, OSError):
                    pass
                raise ProviderUnavailable()
            chunks=bytearray()
            while True:
                remaining=deadline-time.monotonic()
                if remaining <= 0: raise TimeoutError("openai_deadline")
                if connection.sock is not None: connection.sock.settimeout(remaining)
                chunk=response.read1(min(8192,MAX_ENVELOPE+1-len(chunks)))
                if not chunk: break
                chunks.extend(chunk)
                require(len(chunks)<=MAX_ENVELOPE,"openai_response_limit")
            return bytes(chunks)
        finally:
            connection.close()
