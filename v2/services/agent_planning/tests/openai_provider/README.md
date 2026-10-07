# OpenAI provider tests

Owner: Planning/openai_provider. Offline exact-request/output/accounting and injected connection failure checks only. No live key or network in this suite. Test malformed/oversize output,unknown usage,refusal versus abstention,selected Artifact integrity,one request/no redirects/retries and resource cleanup. Live corpus/SQL issuance remains separately gated in evaluation execution.

BP-09.02/B3 unavailable_probe.py is a separately invoked installed-owner process probe. It uses actual loopback HTTP503 and TCP refusal through the explicit test connection factory, retains unavailable versus unknown dispatch status and unknown usage, and verifies no retry/proposal. It reads no real keys and makes no external calls. It does not qualify live provider availability, SQL issuance or billing.
