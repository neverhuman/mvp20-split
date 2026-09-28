# Artifact Acceptance and Fault Entry Points

`installed_probe.py` exercises publication/replay/scoped reads and integrity through an independently installed executable. Owner hosting/config tests remain in this folder and run with `dev/run_tests.py --module data-artifacts --area acceptance` (PostgreSQL requires explicit opt-in).

`fault_host.py` is an explicit test-only executable, excluded from the service wheel. Its stdin configuration selects exactly `upload_synced` or `finalize_committed`. It hosts the real owner API and pauses after actual byte synchronization or actual finalization response generation. A JSON stdout event identifies the upload/attempt or original finalization receipt. The parent must kill this owned process or send `release` on stdin; a 30-second barrier timeout fails. Normal service config rejects fault fields. The host receives only artifact service credentials and never accesses runtime state.

BP-02.06 owns the cross-service recovery orchestration and manifests in runtime tests/acceptance. Hooks are orchestration infrastructure; passing hook-isolation tests alone does not establish process recovery or storage power-loss durability.
