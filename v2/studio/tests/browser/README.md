# Monitor browser boundary tests

Owner: [Monitor presentation](../../src/presentation/README.md). Run `npm run test:browser`; install local Chromium with `npx playwright install chromium` first. This is a separate browser acceptance tier, not part of every Node unit-test run.

`entry.tsx` is a test-only host that constructs the actual `ObservationClient`, `MonitorModel` and `MonitorWorkspace`. Its global model handle exists only for observable test barriers and is not imported by production presentation. `host.mjs` serves the actual bundled browser source and scripted public-schema fixtures through loopback HTTP. It owns no PostgreSQL data, scientific result, gateway deployment or live Runtime authority.

`monitor.mjs` owns seven fresh-context cases: slow detail returns after newer selection; old detail returns after refresh to a new cut; graph denial clears previously visible records; detail-only denial retains the allowed graph; empty scope; expired page requires refresh; expired invalidation cursor automatically resnapshots once. Held HTTP requests are released after the successor observation is visible. The same production browser client performs decoding/cancellation; separate model unit tests prove rejection even when a source ignores cancellation entirely.

Each scenario checks 1440×1000 and 390×844, document overflow, scoped automated A/AA scans and browser exceptions. Screenshots/manifests are written under ignored `v2/.test-results/studio-monitor/<scope>/`. Timing includes assertions and accessibility scans and is diagnostic, not a UI latency benchmark. B2 owns the renderer comparison measurements.

A browser-only defect was found here: native fetch rejects the client instance as its receiver. The production transport now supplies the browser global receiver explicitly; Node-only testing had not exercised that platform behavior. Preserve this real-browser transport route when replacing the harness.

This suite proves consumer behavior against scripted peers. V1 must independently build the consumer and connect it to the actual available Runtime read boundary before child acceptance. Never label these fixture screenshots as live integration evidence.
