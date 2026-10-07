# Local workspace session transport

Owns bounded same-origin session lookup/exchange only. A launcher ticket is sent
once in a JSON POST; no owner token or persistent browser credential storage is
introduced. Cookie handling remains the gateway/browser boundary. Exact context
validation rejects unknown fields and invalid scopes. Requests have a10second
deadline and8KiB response cap. Failures expose only denied/failed states.
Tests: tests/transport/session.test.ts. Actual gateway/browser proof is separate.
