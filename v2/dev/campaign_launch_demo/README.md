# Campaign launch demo qualification

Test/operator tooling for UI-01.06/L4. Builds a new immutable configuration from
the retained scientific demonstration and installs independent Deployment/Gateway
packages. The original configuration and completed campaign remain unchanged.
Prepared drafts replace only the original flat graph's input references with the
exact retained admission ArtifactRefs, preserving scientific nodes and edges.
Runtime public save/validate/admit owns executable acceptance; no peer SQL.

One supervisor owns the installation at a time. Prepare before draining the old
helper, then start the new supervisor with optional launch listener and installed
tool profiles. Secrets are resolved through Deployment vaults, never evidence JSON.
Browser launch and managed workers are required for acceptance; configuration
generation alone grants no delivery credit. All scientific data remain synthetic.

Actual browser proof: studio/tests/integration/campaign_launch.mjs, with launcher
key supplied only through environment. verify_knowledge_review.py --suite launch
--launch-ready <ready.json> supplies the same boundary over LAN with explicit CA
trust and the exact server public-key pin. Only a released previous launch permits
a deliberately new probe. Original-request recovery uses its retained browser state.
Shutdown quiesces native/scientific workers, drains TLS, then Gateway and owners;
the shared demo Controller owns that sequence.

interruption.py is an explicit operator qualification drill. It validates the exact
installed supervisor PID/manifest, waits for a new browser receipt and its bound
pending Docker turn, records safe ownership evidence, then terminates only that
supervisor. It neither stops Docker nor deletes containers/journals. Restart the same
serving configuration and verify the original launch/run/container before acceptance.

LaunchDemoController optionally forwards an explicit in-memory model key to the installed supervisor as AMPHORA_OPENAI_API_KEY. Defaults stay key-free; Deployment exposes it only to explicitly configured live worker bindings.
