# Local acceptance evidence ledger

Owner: BP-09.05/B1. This module checks a frozen, reviewed evidence inventory. It
does not run campaigns, install owners, access databases, evaluate science or
authorize replacement. Only the standard library is used.

`AcceptanceLedger.from_bytes` accepts `deployment-acceptance.v1` with profile
`bp09-local-synthetic.v1`, a forty-character Git baseline, declared host, the
complete gate-to-SHA256 map and exact required limitations. Unknown/missing gates,
duplicate keys, nonfinite JSON and malformed pins reject. Documents are bounded
to 8 MiB each. `verify(directory)` reads only policy-fixed JSON filenames, verifies
their bytes and required status/assertions, and returns one result per gate. It
never follows caller-provided paths from evidence. Direct file/directory links
reject; aliased ancestors and concurrent malicious filesystem mutation are not
covered. Keep evidence on trusted operator-controlled storage.

Run `python -m amphora_deployment.acceptance --ledger FILE --evidence-directory DIR`.
Exit0 means the reviewed bounded evidence set verified; exit2 means rejection.
Diagnostics contain fixed gate/reason labels, not input document content or paths.
No service or provider is contacted. Hash integrity does not establish authenticity,
current health, a clean source build, or the correctness of all nested historical
claims. The frozen manifest needs review; generating new hashes is not acceptance.
Historical evidence keeps its own package versions and campaign identities.

The twelve required gates cover host, installation, live context/model campaign,
corrected successor, capacity, browser, daemon recovery, cold backup, isolated
restore, independent reconstruction, failure proofs and recovery acceptance.
Known worker failures remain required limitations; this module cannot waive them
or claim unattended reliability. Scientific efficacy is explicitly unproven.

Rebuild acceptance: preserve the strict v1 format, required gate set/assertions,
safe error reasons and fail-closed CLI. Tests live in `tests/acceptance` at this
package root; actual frozen evidence and independently installed smoke are separate
BP-09.05 gates. A profile-policy change requires a new version, not reinterpretation
of old ledgers.

Verified 2026-10-07 10:49:15:35 focused tests pass1.34s; core ledger95/95
statements42/42 branches. Whole module119/120 statements43/44 branches99%;
CLI module entry remains outside measured attribution. Actual frozen evidence and
independent installation remain subsequent gates.
