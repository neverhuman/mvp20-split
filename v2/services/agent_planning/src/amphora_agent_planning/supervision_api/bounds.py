"""Whole-body time, bytes and nesting are bounded before command parsing."""

import asyncio
import json

from fastapi.responses import JSONResponse


class RequestBounds:
    def __init__(self, app, *, max_bytes=262144, timeout=10):
        if (type(max_bytes) is not int or not 1 <= max_bytes <= 262144 or
                type(timeout) not in (int, float) or not 0 < timeout <= 10):
            raise ValueError('invalid_request_bounds')
        self.app, self.max_bytes, self.timeout = app, max_bytes, timeout

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        chunks, size = [], 0
        try:
            async with asyncio.timeout(self.timeout):
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect':
                        return
                    block = message.get('body', b'')
                    size += len(block)
                    if size > self.max_bytes:
                        return await JSONResponse({'reason_code': 'request_too_large'}, status_code=413)(scope, receive, send)
                    chunks.append(block)
                    if not message.get('more_body', False):
                        break
        except TimeoutError:
            return await JSONResponse({'reason_code': 'request_timeout'}, status_code=408)(scope, receive, send)
        body = b''.join(chunks)
        try:
            pending = [(json.loads(body), 0)] if body else []
            while pending:
                value, depth = pending.pop()
                if depth > 64:
                    raise RecursionError
                if isinstance(value, dict):
                    pending.extend((item, depth + 1) for item in value.values())
                elif isinstance(value, list):
                    pending.extend((item, depth + 1) for item in value)
        except RecursionError:
            return await JSONResponse({'reason_code': 'nesting_limit'}, status_code=422)(scope, receive, send)
        except (ValueError, UnicodeError):
            return await JSONResponse({'reason_code': 'invalid_json'}, status_code=422)(scope, receive, send)
        delivered = False
        async def replay():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type': 'http.request', 'body': body, 'more_body': False}
            return await receive()
        return await self.app(scope, replay, send)
