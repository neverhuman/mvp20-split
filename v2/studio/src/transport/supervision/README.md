# Supervisor inspection transport

Owner: Studio,BP-07.05/B1.04.

SupervisionClient implements five GET-only Runtime public surfaces through /api/runtime. Strict generated DTO decoding,262144-byte cap,ten-item pages,timeout/abort,scope/run and nested metadata scope checks,decision/request binding and snapshot coherence.401/403 denied,404 unavailable,409/410 resnapshot,other errors sanitized. No backend credentials,content retrieval,execution commands or peer state. Browser gateway is a test/deployment boundary,not implemented production authentication. Owned tests: tests/transport/supervision.test.ts.

Replacement must preserve public wire contracts,scope isolation,coherent page boundaries and truthful states. Python supervision schemas remain authoritative.
