"""A slow sender cannot retain the request parser indefinitely."""

import asyncio

from amphora_campaign_runtime.api import RequestBounds


def test_whole_body_deadline_returns_sanitized_timeout():
    async def probe():
        messages = []
        async def downstream(*_args):
            raise AssertionError("Incomplete request must not reach handlers")
        async def receive():
            await asyncio.sleep(1)
            return {"type": "http.request", "body": b"private", "more_body": True}
        async def send(message):
            messages.append(message)
        await RequestBounds(downstream, body_timeout=0.01)({"type": "http"}, receive, send)
        assert messages[0]["status"] == 408
        assert b"private" not in messages[1]["body"]
    asyncio.run(probe())
