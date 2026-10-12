# Local browser gateway

Current release0.5.0 adds UI-01.07 exact Planning campaign-origin GET, with two
strict query pins,256KiB response bound and distinct sanitized absence/denial/
inconsistency states.58 independent tests and actual local/LAN provenance traversal
pass2026-10-11 19:26:42. No new write, provider or operator route.

Historical release checkpoints follow.

Owner LAN-01/UI-01.06; release0.4.0 adds the explicit Deployment launch peer.
Only /v1/campaign-launch-profiles, /v1/campaign-launches and one receipt identity
are routed; no query parameters or operator controls. Launch POST is bounded to
262144bytes. Safe allowlisted launch reason codes survive error sanitization;
all other upstream details remain private. Cookie/origin/host gates and server-side
bearer injection still apply. Cross-owner HTTP fixture verifies session, denied origin,
duplicate request/receipt and active-slot collision; actual UI campaign remains L4.
Release0.3.0 introduced the explicit HTTPS LAN profile. This independent service owns
loopback Studio hosting, browser sessions and bounded public HTTP routing to the
six service owners. It owns no campaign decisions, SQL/schema, scientific policy,
provider requests or private service imports. Studio remains a separate package.

`lan-gateway-v1` adds a required listener object with address, subnet, certificate
and private_key. Bind only a specific RFC1918 IPv4 address within its explicit
/16 to /30 private client subnet; certificates and keys are absolute local files.
TLS1.2 minimum, exact Host/HTTPS Origin, Secure HttpOnly SameSite cookie, and
source-subnet filtering apply. Owner peers remain loopback. Only requests from
the listener's own address may issue tickets, using the existing launcher key.
LAN tickets expire after300seconds, single use; sessions retain the8hour bound.
Local profile defaults, localhost launch command and cooperative drain are unchanged.
This is trusted internal LAN demo access, not internet or multi-user deployment.
Operators supply certificate trust and firewall configuration; this package does
not change either. `dev/serve_lan_review.py` owns the local demo operator workflow.
Optional serve --stop-file watches a local operator marker and stops acceptance,
then cooperatively joins accepted requests through the existing close behavior.

The initial local user opens the workspace through a local launcher. A single-use,
60-second ticket travels in the URL fragment and is removed before session exchange;
long-lived owner credentials remain server-side. Sessions last at most8hours,
are revocable and are invalidated by gateway restart. Ticket/session capacities
are16/8 respectively. Tokens are indexed only by SHA256 in memory. These limits
bound local session state; they do not assert multi-user authorization readiness.
Session, HTTP transport and browser integration have module-scoped tests.

Browser boundary: host-only HttpOnly SameSite=Strict session cookie on
127.0.0.1; exact Host and Origin checks for unsafe requests; no CORS; fixed owner
routes and server-side bearer injection. Owner response bodies stay byte-preserved
within explicit bounds. No redirects, proxy environment routing or upstream cookies.
Readiness remains owner authority; a reachable gateway is not a ready campaign.

User task: inspect an autonomous campaign, then prepare next-campaign changes.
Reuse existing Monitor/Design/Explore models and presentation tokens. The entry
surface owns session/loading/denied/expired and no-selected-campaign states;
existing owner-backed page models own run/evidence/draft loading and failures.
No sample campaign may be presented as live data. Full owner/browser acceptance
is separate from fixture transport verification. Tests remain module-scoped.


`python -I -m amphora_local_gateway serve --config <path> --port <loopback-port>`
loads the reviewed local-gateway-v1 configuration. It names the static directory,
explicit loopback peers/token environment references, launcher-key reference and
browser actor/scope/optional selected run/synthetic label. It neither discovers
nor starts owners. The public assets are exactly index.html, app.js and app.css,
each at most16MiB. At most16 request threads are admitted. Requests are bounded to
1MiB and owner responses to8MiB; socket operations time out after15seconds.
Owner response errors are sanitized while preserving status. Executable/unknown
upstream media types are exposed as octet-stream with nosniff; raw bytes stay
unchanged. No retained artifact becomes executable JavaScript/HTML on Studio's origin.

The `launch --endpoint <loopback-url> --key-env <reference>` command issues a ticket
using the environment key and opens its URL fragment in the browser. It prints
neither the credential nor ticket. Gateway restart invalidates all tickets/sessions.
No encrypted credential files are read by this package; Deployment owns those files
and selects the environment grants. The browser uses only its opaque HttpOnly cookie.

Studio0.9 builds assets with `npm run build:local`; schema validators are compiled
before bundling, so script-src self remains intact without unsafe-eval. Browser
proof covers session denial, fragment consumption in reused tabs, cookie flags,
logout, empty state and Monitor with an explicitly synthetic public HTTP peer,
1440/390width layouts and serious/critical accessibility checks. Separate injected
slow/unavailable-session cases verify presentation states, not backend behavior.

Release0.3:32 independently installed owned Python tests pass, including HTTPS
session exchange, bounded LAN profile, ticket expiry and cooperative CLI stop.
Historical0.2 coverage:346statements/46missed and46branches,86% combined coverage;
that percentage is not a fresh measurement of0.3.
CLI exceptional startup, thread saturation, socket loss/truncation and some handler
failure branches remain gaps. Live six-owner readiness and graceful application
drain belong to BP-09.02/B2; campaign/model demonstration belongs to BP-09.03.
Replacement preserves request limits, public wire bytes, origin/session checks and
sanitized failures; recreate sessions explicitly after process replacement.

Release0.2 retains accepted request threads during server_close. KeyboardInterrupt
stops accepting new connections, then joins those requests; the Deployment supervisor
reports an unresolved drain after45seconds without silently killing the process.
An actual blocked proxy response test proves close waits for full response completion.
Socket timeouts bound inactivity, not total wall time against a trickling peer.
Forced supervisor death remains an interruption requiring normal owner reconciliation.

UI-01.07/Gateway0.5 adds strict forwarding for Planning campaign-origins: exact
draft/revision/digest, GET with no body, no broad/history paths,256KiB response limit.
Only named origin failure codes cross the proxy; arbitrary owner details remain
redacted. Configure a Planning peer token with read_campaign_origin for the viewer's
scope; no caller-selected credentials or write grants are introduced. Existing peer
routes remain unchanged.69 combined Gateway/API transport checks pass; live deployment
and browser qualification remain pending.

## Curation and capability routes (UI-01.08/P3.3a)

curation_routes.py owns exact approved Planning family paths and GET/POST pairs.
Curation collection/receipt query use POST; exact curation/capability reads use GET;
fulfillment uses only the approved per-request POST. Query additions, extra path
segments, lookalike families, GET bodies and wrong methods reject before forwarding.
Requests are bounded256KiB and successes1MiB; named owner errors are reduced to a
closed reason-code allowlist with4KiB parsing. No private diagnostic fields cross.
Gateway grants no new owner permissions, model work or verification authority.
Planning credentials and original scoped commands remain authoritative. Earlier
provenance, launch and legacy routes retain their existing bounds. Source-only;
serving demo unchanged. Tests: tests/transport/test_curations.py plus transport
regressions. Browser consumes published Planning contracts, never peer implementation.

Gateway0.6 curation boundary qualified:84 source/boundary checks and78 fresh-wheel
checks, including localhost HTTP/TLS and legacy transport. Independent evidence:
curation-gateway-installation-20261012a/evidence.json. No live demo upgrade.
