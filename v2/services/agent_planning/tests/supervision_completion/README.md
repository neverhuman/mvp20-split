# Completion tests

Actual Planning PostgreSQL tests cover zero-call stop/replay, immutable grants, read-only access, successful settled history, original ticket replay, new-issuance fencing, retained unissued reservations, in-flight completion conflict and exact authenticated HTTP readback. Data and provider are scripted fixtures; HTTP uses FastAPI TestClient. No live science or separate installed owner proof.

Run `dev/run_tests.py --module agent-planning --area supervision_completion` with `AMPHORA_TEST_POSTGRES=1`. Planning0018 must be available; never run older migrators against this fixture.
