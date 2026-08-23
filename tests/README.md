# tests/

**These are NOT the Amphora test suite.** This directory holds only the Python tests for the
NOMAD Crystal360 program (`pytest tests/crystal360`).

Amphora's tests are:

```bash
cargo test --workspace --locked          # the Rust workspace, incl. per-module tests/
ops/amphora-controller/tests/run.sh      # controller unit tests
ops/amphora-controller/tools/tests/run-all.sh
pytest benchkit/tests                    # the numerical benchkit package
```

See [../BUILD.md](../BUILD.md).
