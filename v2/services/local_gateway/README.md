# Local browser gateway

Owner BP-09.02; release0.2.0 adds cooperative request drain. This independent service owns
loopback Studio hosting, browser sessions and bounded public HTTP routing to the
six service owners. It owns no campaign decisions, SQL/schema, scientific policy,
provider requests or private service imports. Studio remains a separate package.

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

27 owned Python tests pass;346statements/46missed and46branches,86% combined coverage.
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
