# dispatch-boundary-fail-closed-v1

Independent non-runtime oracle for **amphora-redteam-audit** covering the meta-audit's
**INPUT dispatch fail-closed boundary** — the KPI `unsupported_module_id_fail_closed_rate`,
which ships only 6 probes. Distinct from and non-overlapping with the prior fire
`meta-integrity-oracle-parity-v1` (that oracle covered OUTPUT-payload digest parity + a
result-tamper corpus; it did NOT independently reproduce the input dispatch boundary).

Falsifiable hypothesis (mission): "a locked adversarial corpus detects malformed envelopes
and authority escalation." Here specialized to the dispatch surface: the runtime dispatch
is a **fail-closed exact-byte-match allowlist** `accept(id) ⟺ id ∈ S`, S = the 9 shipped
supported modules.

Gates (all PASS, verdict HYPOTHESIS_CORROBORATED):
- **G1 supported-set derivation** — S derived from `result.v1.json` records equals the 9
  mission-declared modules exactly, |S|=9, no duplicates, matches KPI dispatch sample_size 9.
- **G2 shipped-probe reproduction** — the 6 shipped `unsupported_module_id_fail_closed_rate`
  probes ("", "   ", amphora-does-not-exist, amphora-source_ledger, AMPHORA-REDTEAM-AUDIT,
  Cyrillic АМФОРА) each independently fail-close under exact-match; independent verdict
  agrees with shipped `fail_closed=true` on 6/6.
- **G3 positive-control acceptance** — all 9 genuine ids accept (complete mediation; no
  genuine dispatch is wrongly denied).
- **G4 near-miss adversarial fuzz** — 171 deterministically-generated near-misses across 19
  mutation families (case, whitespace/tab/newline, trailing dot/slash, path-traversal,
  hyphen→underscore/space/removed, zero-width-space, trailing-null, sub/super-string,
  Cyrillic homoglyph) over all 9 ids: **171/171 fail-closed, 0 accidental exact collisions**.
- **G5 exact-match necessity** — two named relaxations each WRONGLY admit a shipped probe:
  a case-insensitive relaxation admits `AMPHORA-REDTEAM-AUDIT`; a Unicode-TR39
  confusable-skeleton relaxation admits a Cyrillic homoglyph of a real id — while
  exact-byte-match correctly rejects both ⇒ exact-byte membership is load-bearing.

Theory: Anderson 1972 reference-monitor / complete mediation; Saltzer-Schroeder 1975
fail-safe defaults; NIST SP 800-53 Rev.5 AC-3/AC-6 deny-by-default; Unicode TR39 confusable
skeleton (2023); RFC 8785 JCS; NIST FIPS 180-4 SHA-256.

Run: `python3 oracle_dispatch_boundary.py` (stdout is byte-stable; == result.v1.json,
SHA-256 `021e1895f5cec9fc45a20d1ea85cbf6eccca6f1397d593c72c01f191f19e6c1d`).
Sign: `python3 sign_dispatch_boundary.py`.
Signed AUDIT_ONLY receipt: `../../evidence/phase0/independent/dispatch-boundary-fail-closed-v1.dsse.json`
(phase0-evaluator key `3ef6b35c…`, DSSE PAE + Ed25519).

Ceiling: models dispatch as exact-byte-match membership over the shipped accept-set and
reproduces the 6 KPI probes byte-exact, but does NOT re-execute the Rust dispatch fn
`deterministic_control_diagnostic`. Live Rust dispatch re-execution + full error-taxonomy
parity remain the Phase-1 axis. AUDIT_ONLY — no promotion, no authority, manifest untouched.
