"""One direct TLS request, no redirects/retries/proxies or remote tool execution."""
import http.client
import time

from ..context.policy import require
from ..providers.port import ProviderUnavailable

MAX_ENVELOPE = 1048576

class OpenAIHTTP:
    def __init__(self, api_key, *, timeout_seconds=45, connection_factory=http.client.HTTPSConnection):
        require(type(api_key) is str and bool(api_key) and "\n" not in api_key and "\r" not in api_key, "openai_credentials_missing")
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 60, "openai_timeout")
        self._key,self.timeout,self.factory = api_key,timeout_seconds,connection_factory
    def send(self, body):
        require(type(body) is bytes and 0 < len(body) <= 8192, "openai_http_body")
        deadline=time.monotonic()+self.timeout
        connection=self.factory("api.openai.com",timeout=self.timeout)
        try:
            connection.request("POST","/v1/responses",body=body,headers={"Authorization":"Bearer "+self._key,"Content-Type":"application/json","Accept":"application/json"})
            remaining=deadline-time.monotonic()
            if remaining <= 0: raise TimeoutError("openai_deadline")
            if connection.sock is not None: connection.sock.settimeout(remaining)
            response=connection.getresponse()
            if response.status != 200:
                # Never retain provider error bodies, which may echo submitted secrets/content.
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
