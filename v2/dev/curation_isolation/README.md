# Provider schema isolation

Owner-directed2026-10-12 18:25:06, UI-01.08/P5.2 blocking diagnosis. This dev-owned
probe uses the production direct HTTPS transport/diagnostic capture and pinned model,
synthetic prompts, fresh process per case, no retries. It never admits a campaign,
changes acceptance schemas or rewrites any prior request or campaign reservation.

Self-imposed diagnostic ceiling16 originals x$0.03=$0.48; serialized request plus
1024 conservative input tokens is bounded32768, output512. Original exclusive disk
reservations precede transport; failure/uncertainty does not refund. A leftover lock
fails closed. No imports read credentials; explicit --live reads the authorized
SSOS key, never prints/stores it. No reasoning text or arbitrary remote errors saved.
Visible diagnostic output is explicitly not an accepted campaign proposal.

Initial ladder: tiny strict object, narrowed/pruned abstention schema, full structure
without constraints, full schema without patterns, original full schema. Select one
case explicitly, inspect results, then choose the next. Stop once the failing feature
is isolated; retain passing prefix. Offline tests own transforms and spend boundaries.

Completed eight-case series: +/-1e100 bounds trigger the failure even in a tiny
schema; full schema passes with only these bounds omitted. Original structure case
was an invalid probe (field named minimum stripped); schema-aware traversal and
regression test repair it in structure-v2. Original case retained. Probes stopped.
