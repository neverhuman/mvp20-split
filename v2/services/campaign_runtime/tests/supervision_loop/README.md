# Checkpoint driver verification

Run Runtime area `supervision_loop` with `AMPHORA_TEST_POSTGRES=1`. Tests use actual admitted Runtime SQL state and explicitly scripted public Planning/Data boundaries. They preserve fixture history and test bounded stage progression, immutable winner replay, concurrent repair, original deadline/allowance authority, and pre-call failures without invented observations. Socket components are covered in supervision_delivery/outcomes; installed multi-owner and scheduling proof remain separate BP-07.04 gates.

Actual multi-owner scenarios are isolated in [owners](owners/README.md) and require a separate AMPHORA_TEST_OWNER_PROCESSES=1 opt-in. Routine module SQL checks keep their existing smaller scope.

`test_process_recovery.py` explicitly invokes process_probe.py in separate pytest processes. It kills by abrupt exit after request persistence or response/report persistence, then restores the exact request or accepts once. Teardown cancels only the probe campaign through Runtime authority. Actual SQL; scripted Planning exchange; installed replacement remains V1.
