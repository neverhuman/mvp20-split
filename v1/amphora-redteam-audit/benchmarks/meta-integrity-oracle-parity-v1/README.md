# meta-integrity-oracle-parity-v1

Independent non-runtime CPython oracle for **amphora-redteam-audit** (module had 0
scientific receipts). Re-derives the meta-audit integrity guarantees the Rust runtime
asserts, WITHOUT invoking that runtime, and reproduces the shipped byte-exact digest
anchors; then runs an independently-constructed adversarial tamper corpus.

Falsifiable hypothesis (mission): "a locked adversarial corpus detects malformed
envelopes and authority escalation."

Gates (all PASS, verdict HYPOTHESIS_CORROBORATED):
- G1 digest parity: independent canonical-JSON + SHA-256 stable_hash reproduces the
  shipped diagnostic_sha256 (a873469357434995...) byte-exact, both replays.
- G2 raw-hash anchors: benchmark_lock_sha256 + dataset_fixture_sha256 reproduced from raw bytes.
- G3 attack-axis coverage: 24/24 canonical REDTEAM axes present in benchmark-lock AND
  cross-checked true in the result axis_details.
- G4 authority-envelope: 0 forbidden authority-escalation keys anywhere; 9/9 records
  carry all 10 zero-authority claim locks; module-id set matches the 9 supported modules.
- G5 replay byte-stability: first/second replay canonically identical.
- G6 adversarial tamper detection: 8/8 independent mutations (flip passed_flag, drop axis,
  inject batch_release / release_authority, alter result_digest, fabricate record, strip
  claim lock, false execution-completion) DETECTED; no-op control not flagged.

Theory: RFC 8785 JCS; FIPS 180-4; Ed25519 (RFC 8032 / CHES 2011); in-toto DSSE v1.0;
Anderson-1980 reference-monitor / Saltzer-Schroeder-1975 / NIST SP 800-53 AU-6,CM-6.

Run: python3 oracle.py  (stdout is byte-stable; == result.v1.json).
Signed AUDIT_ONLY receipt: ../../evidence/phase0/independent/meta-integrity-oracle-parity-v1.dsse.json
(phase0-evaluator key 3ef6b35c..., DSSE Ed25519). Ceiling: offline oracle over shipped
evidence; Rust error-taxonomy parity + live-runtime re-execution = Phase-1.
