# Managed worker turns

Owner: BP-09.03/B1.3b, Deployment0.9. Native controller/configuration independently
qualified; scientific containers and catalog reporting have separate sibling modules.
No workers are active in the accepted read-only serving profile.

Deployment owns process lifetime, not graph scheduling. Runtime's coordinator,
artifact delivery and checkpoint loop, and Planning's checkpoint worker retain
their existing public CLIs, permissions, database ownership, claim/replay and
deadline rules. Five closed native recipes request two-second sweeps, with one
second between polls; an in-flight operation can exceed the sweep window.
Runtime delivery now permits at most100items within that same two-second sweep,
the existing owner CLI's supported ceiling. The earlier ten-item batch left artifact
confirmations waiting behind retries for unconfigured notification targets during
the actual numeric campaign. Increasing the bounded batch changes neither receipts,
retry policy nor acknowledgement authority; unavailable notifications remain visible.
Actual original-backlog recovery confirmed all15 output reservations in25.44seconds
within the unchanged120second gate, with identical completed graph and no scientific
reruns. Fresh full-campaign and independent-installation evidence is owned by the
active BP-09.03 tracker; recovery alone is not whole-campaign acceptance.

WorkerSlot allows one live turn per slot. Explicit start enables repeated turns;
only exit zero permits repetition after a bounded interval. Nonzero exit or
uncertain launch/observation/cleanup latches failure and disables new turns.
Status never launches work. Explicit recovery reconciles the binding; start is
separate. Quiescence disables new turns and waits for the current turn's actual
exit without signals, interruption or timeout-based success. Failure must be
reconciled before the quiescence guard passes. Supervisor enforces the guard
before owner drain/restart/force-stop or normal shutdown. Owner process loss
quiesces all workers without interrupting active turns. Readiness is separately
verified; a running owner is only a necessary condition for starting workers.

NativeBinding pins configuration, source-lock and installed-owner inventory
identities; every launch and recovery rechecks those bytes. Scope is explicit
for coordinate/deliver and owned by configuration for checkpoint workers.
Only explicit AMPHORA_ environment values plus minimal Windows system variables
reach children. Secrets are excluded from repr, raw child output is discarded,
and no shell or user-supplied command is accepted. The pin is an accidental-drift
guard, not protection against malicious same-user file replacement. Configuration
pins include Planning templates and Runtime graph definitions, release descriptors,
schemas and admission policies/recipes. Referenced files must be relative children
of the configuration directory, bounded individually and in aggregate.

The optional `--workers-manifest` for lifecycle serve selects a separate immutable
`local-native-workers-v1` sidecar; existing `local-supervisor-v1` bytes are unchanged.
Its workers map names a subset of the five native recipes. Each entry contains
configuration/source_lock absolute paths and scope (null for checkpoint workers;
actor/tenant/project for coordinate/deliver). Workers must use exactly the serving
owner's pinned installation and inherit only that owner's scoped environment.
Live Planning additionally requires the explicit configured synthetic-only policy
and AMPHORA_OPENAI_API_KEY from the controller environment. No .env reader, key
default or provider call occurs during binding. The Planning owner still enforces
original reservation, cost, deadline, context and dispatch rules.

Authenticated body-free control adds POST /workers/{name}/{start,quiesce,recover,
force-stop}; CLI uses the same action and `--worker`. GET /status includes workers
only when configured, preserving the existing no-worker shape. Controller ticks
launch turns but never admit/select graph work. Normal shutdown uses the existing
writer lease; unexpected controller teardown forces owned native jobs. The sidecar
must be reloaded through a stopped-controller replacement to change pins.

NativeTurn gates module entry until its live process handle is attached to an
unnamed kill-on-close Windows job. It has no interrupt/drain pipe command.
Normal release requires observed process exit. Explicit forced teardown and
controller death can terminate active work and must not be reported as graceful
quiescence. No stored PID is accepted as recovery or termination authority.

Tests live in deploy/local/tests/workers. Pure state transition tests cover
repetition, failure latching, retained uncertain handles and noninterrupting
quiescence. Windows process tests must separately prove real job behavior.
Owner readiness, successful campaigns, actual provider effects and Docker
ownership are separate integration gates, not established by these primitives.

Verified 2026-10-07 01:22:21:164 source tests26.79s; independent a/b each164tests and
actual installed Runtime0.65/Planning0.101 empty-scope sweeps with API drain409,
quiescence and owner exits0; rebuilt wheel hashes identical. Final38worker tests
3.54s cover281/292statements44/50branches94%. Aggregate forced cleanup, observation
failure and some manifest variants remain coverage gaps; actual probe separately
exercises disabled-provider loading. No campaigns or model calls.

UI-01.08j/M1 adds planning-curation, invoking Planning's curation_worker run CLI
with the same bounded two-second sweep and noninterrupting shutdown semantics.
Its scope/actor/peer references belong to the pinned owner configuration; sidecar
scope is null. Pin1..32 unique relative policy files as well as the worker file.
Only disabled or explicit openai_curation_v1 is allowed; live composition requires
AMPHORA_OPENAI_API_KEY plus synthetic-only policy. Disabled mode does not import
that key. Owner serving environment and installation must match; no peer-private
state or graph scheduling enters Deployment. Planning retains original holds,
discovery/claims/dispatch and all execution acceptance. M2 installed lifecycle
and M3 actual demo delivery are separate acceptance gates.
