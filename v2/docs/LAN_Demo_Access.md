# Local network demo access

Verified 2026-10-08 10:08:00 America/Chicago. LAN gateway0.3.0 is serving
https://192.168.1.70:57013 alongside the existing http://127.0.0.1:57013 gateway.
Both show the same retained synthetic campaign. Remote-computer acceptance is pending.

## Open from another computer

1. Copy `v2/.test-results/lan-live-20261008a/amphora-demo-ca.cer` to that computer.
   On Windows, open it, choose Install Certificate, Current User, then explicitly
   select Trusted Root Certification Authorities. This trusts only the locally
   generated demo CA; its certificate expires after seven days. Remove it after
   the demonstration if access is no longer needed. Never transfer private keys.
2. On the hosting computer, run `New Invitation.cmd` in the same session folder.
   It copies a fresh sign-in URL to the clipboard and creates `Open Amphora.url`.
   Send that URL or shortcut to the other computer and open it within five minutes.
   Each invitation works once. Do not open it locally before sharing it.
3. The browser session lasts up to eight hours. Bookmark the plain HTTPS address
   after signing in. A gateway restart requires a fresh invitation.

The owner added firewall TCP57013. A connection timeout points to the network or
firewall path; a certificate warning means that path works but trust is unfinished.
Do not use HTTP for the LAN address: browser artifact verification requires HTTPS.
Client addresses must be within192.168.1.0/24; owners and databases stay on loopback.
The exact-IP binding must be updated if the host's DHCP address changes.

## Operator continuity

Live session: `v2/.test-results/lan-live-20261008a`; isolated gateway installation:
`v2/.test-results/lan-gateway-20261008a`. Original localhost session remains
`v2/.test-results/connected-flow-live-c`. No scientific workers or provider calls.
The LAN helper started2026-10-08 10:04:28 with an86400second limit. Original owners
are scheduled to stop2026-10-09 06:01:36, which also ends useful LAN service.
Create `STOP` inside only the LAN session folder to drain the separate gateway.
Do not stop the original owner supervisor during the demonstration.

Repeatable helper: `dev/serve_lan_review.py serve` requires --root deployment-root,
--session new-output-directory, --baseline existing-gateway.json, --tls private-TLS-directory,
and --python isolated-gateway-python. `invite` needs only --root and --session.
The generated shortcut contains a short-lived access token; do not commit or log it.
CA public fingerprint SHA256 is available with `certutil -hashfile amphora-demo-ca.cer SHA256`.

Verification:32 independently installed gateway tests; CA-verified HTTPS API;
browser uses an exact server public-key pin rather than global certificate bypass.
Full five-view HTTPS walkthrough and localhost regression pass, including WebCrypto,
content verification,1440/390 layouts and accessibility. This proves host-side HTTPS
behavior; it does not substitute for the second computer's firewall/trust check.
