# Local network demo access

- Status: implemented; second-computer acceptance pending.
- Last refreshed: 2026-10-08 10:10:00 America/Chicago.
- Completion: 100%; L1 gateway boundary100, L2 installed/browser verification100,
  L3 actual listener/operator handoff100. Three equal implementation gates.
- Acceptance: owner confirmed second-computer reachability2026-10-08 10:26:00 after correcting HTTP to HTTPS; authenticated walkthrough/trust pending, separate from implementation.
- Current: live https://192.168.1.70:57013; original localhost preserved.
- Next: owner remote connectivity/trust check, then return to paused UI-01.
- Owner added firewall rule for TCP57013. Do not replace unrelated firewall rules.

Use exact192.168.1.70 binding and192.168.1.0/24 client boundary; no backend listener
changes. Localhost keeps its original HTTP gateway and campaign. HTTPS is necessary
for browser Web Crypto content verification on a non-loopback origin. An explicitly
configured LAN profile adds certificate/key paths, subnet and an exact HTTPS origin.
Default local profile and byte-preserving owner proxy remain unchanged. Long-lived
owner keys remain server-side; browser access uses single-use session tickets.

Create scoped local TLS material and a repeatable operator launcher/link helper.
No anonymous owner access, CORS broadening, peer SQL, owner reconfiguration or
scientific/provider calls. Client certificate trust and final remote access may
require the owner's second computer; finish all local verification first.

L1: validate profile, bind/subnet/origin rules, TLS and secure cookie behavior.
L2: isolated install, scoped regression and actual HTTPS Studio traversal/content
verification. L3: preserve original demo, serve LAN address/port, inspect the owner
firewall rule and provide concrete second-computer steps. Record actual evidence
and unresolved external acceptance separately. UI-01/LR-01 work remains paused.

Activation coherence:2026-10-08 09:52:14, owner authorized LAN priority; existing
isolated gateway and same-origin assets can be reused. Browser WebCrypto requires
HTTPS off loopback; no owner routing/API or scientific behavior changes necessary.

L1 exit: additive Gateway0.3 profile and certificate/subnet/origin/session controls.
L2 exit: independent wheel installation,32 owned tests, production boundaries;
actual HTTPS five-view traversal and localhost regression both pass.
L3 exit: actual listener live2026-10-08 10:04:28, existing owner process preserved;
[operator runbook](../LAN_Demo_Access.md) and invitation helper available. Firewall
inspection denied to this nonadministrator; owner reported the rule installed.
Remote path validation is explicitly pending, not claimed by host-local probes.
[Scoped audit](../Audits/LAN-01_Demo_Access.md) records evidence and acceptance limits.
