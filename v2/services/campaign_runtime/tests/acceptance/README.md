# Installed Runtime Acceptance

This runtime-owned acceptance tier runs outside the checkout against independently installed wheels. It uses public HTTP contracts for assertions; migration/bootstrap remains development tooling responsibility. Synthetic fixtures prove software behavior, not scientific validity.

`installed_probe.py` starts a runtime host and HTTP-only workers, kills a claimed worker, waits for actual lease expiry, and checks successor fences, original receipts, scoped reads, revocation and budget settlement.

`integrated_probe.py` starts runtime and artifact hosts in separate installed environments. Each service receives only its own restricted database credential. HTTP worker subprocesses receive no database credential. Actual uploaded/finalized input and output bytes feed completion; public reports and artifact reservation reads independently expose acceptance, confirmation and cancellation/release. `paired_support.py` supplies test-only process/HTTP plumbing and a forwarding reservation barrier. It pauses an actual owner response after protection; it never fabricates an outcome or changes production startup.

The integrated oracle checks output/checkpoint reservations before and after delivery, exact committed outcome proof, original completion receipt replay, conserved budgets, and an aborted binding released before the stale completion resumes. Services and the forwarding proxy are stopped by the owning harness. Scope identities are unique; no shared database reset or cross-owner SQL is used.

Run through `dev/verify_foundation.py --builds` with `AMPHORA_TEST_POSTGRES=1`. Tooling builds eight packages, installs each with its public dependencies outside the source tree, verifies the peer service package is absent, and supplies the two executable paths and isolated fixture credentials. Standalone invocation requires the two scoped service database URLs in environment and the installed artifact Python path as the positional argument. Never log credentials.

The broader named process-kill/restart matrix belongs to BP-02.06. Passing these probes does not establish host power-loss durability, target filesystem semantics, deployment readiness, general graph execution or scientific efficacy.
