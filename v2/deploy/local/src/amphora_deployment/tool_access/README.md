# Local tool TLS access

Owner: local Deployment, BP-09.03/B1.3. Architecture: [Runtime topology](../../../../../docs/Architecture/System/Runtime_Topology.md).
This module provides a TLS identity and forwarding boundary for Linux containers accessing
Windows loopback owner APIs through host.docker.internal. It owns no campaign/tool execution,
SQL state, upstream credentials, browser sessions or scientific authority. Runtime/Data still
authenticate each original bearer token and validate their public operations.

Current implementation: TLSIdentity provisions a create-once30-day self-signed server certificate
for host.docker.internal using an explicitly supplied OpenSSL executable. It records executable,
certificate and encrypted-key hashes. An encrypted PEM private key remains at rest; its random
password is protected in a separate current-user DPAPI vault bound to deployment identity.
No plaintext private key, global trust installation, silent rotation or regeneration. Partial
provisioning fails closed and remains inspectable. Existing files cannot be overwritten. Key/
certificate/hash/password compatibility is checked before serving; TLS minimum1.2. Python's
runtime TLS library handles live connections; OpenSSL CLI is only offline provisioning.

ToolAccessServer listens only on127.0.0.1, forwarding to one fixed Runtime or Data loopback port.
The caller must provide exactly one bearer header, correct Host and bounded /v1/ path/body.
Incoming headers cannot choose upstreams. Proxy/environment redirects are never used. The
original bearer/body/method/path go upstream; cookies and other headers do not. Only bounded
status/body/content-type return. Authentication denial remains the owner's response. Diagnostics
never echo payloads, headers, credentials or exception tracebacks.

Eight connections by default, at most16, with handshake/read timeouts and30-second forwarding
deadline. Bodies/responses are capped16MiB, conflicting lengths/chunked input are rejected.
One request per connection; accepted threads are non-daemon and server_close waits for them.
That transport drain is not worker/campaign quiescence. Optional local-tool-access-v1
configuration binds the original deployment identity and unique TLS ports to persisted
Runtime/Data loopback routes. Controller-owned AccessListeners start explicitly, drain
asynchronously and wait for accepted responses. Supervisor enforces workers -> TLS -> APIs
shutdown order and quiesces workers when a configured TLS listener becomes unavailable.
Repeated start retains the listener; restart requires its actual exit and rechecks identity.
The controller keeps its installation writer lease through listener cleanup. No scientific
container lifecycle is implicitly started by opening these transports.

Container trust must explicitly mount the public certificate and select SSL_CERT_FILE. Never
disable validation or relax SDK HTTP restrictions. Certificate expiry/replacement needs a new
reviewed configuration between campaigns. DPAPI protects storage against other users, not the
same user or administrators; TLS connectivity is not an egress sandbox. Tests live beside this
module under deploy/local/tests/tool_access; actual container/SDK acceptance is a separate gate.

Verified `2026-10-07 00:58:38`:125deployment regressions passed; final16TLS tests15.54s.
Independent Deployment0.3 passes126 tests and actual Linux evolution0.5/SDK0.2 trust/denial
probes through a synthetic upstream. Coverage224/247 statements,36/44 branches (89.35%
combined). Remaining paths include connection-cap/thread-start failures, some timeout/socket
errors, alternate response framing/media and Expect handling. No100% or actual-owner claim.
