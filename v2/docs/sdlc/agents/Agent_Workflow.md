# Agent workflow and handoff

Reviewed: 2026-10-16 14:17:15 America/Chicago. Canonical development process; not evidence of implementation.

Read AGENTS and Restore, then the [SDLC index](../README.md) and the process page relevant to the current task. Select work from MBT and its canonical tracker. Read history only when current summaries fail. Maintain a concise exact return point across interruptions/compaction.

Existing user authorization persists; process pages add no approval ceremony. Delegation follows session instructions and is not implied by a checklist. Historical external paths are provenance, not permission to access another workspace. Leave Input.md empty unless the owner populates it. Keep credentials and local datasets out of Git.

## Continue-until-needed operating rule

- When the owner says to continue until needed, that authorization persists across milestones, commits, pushes, plan boundaries and context compaction. After satisfying the current gate, update canonical trackers and Restore.md, commit/push significant verified work, then immediately take the next authorized task in MBT order.
- A completed milestone, clean working tree, passing tests, successful push or updated handoff is a progress checkpoint, not a reason to end the turn. Report those checkpoints in commentary and keep working. Do not end with "no user decision needed" while authorized work remains.
- Stop only when the authorized scope is complete, the owner pauses/redirects work, or a concrete decision, permission or external blocker prevents further authorized progress. Explain the specific blocker and the smallest owner action needed; complete independent authorized work first. Do not invent approval gates or blockers to justify stopping.
- Context pressure is a reason to refresh Restore.md and preserve exact state, not to request another "continue." Resume from that handoff after compaction. Keep bounded phases, prerequisite gates, scoped verification and audit requirements intact; autonomy does not waive them.

## Context window and token discipline

- Treat context capacity and token consumption as related but distinct constraints. Use the available context window when it improves reasoning, integration accuracy, or design continuity; avoid consuming tokens on low-signal history, generated dumps, broad logs, or repeated reads.
- Use `rg`, `git diff --stat`, targeted `Get-Content -TotalCount`, and `Select-Object -Skip -First` before reading full files. Read full files only when the local context is genuinely required.
- Avoid reading generated inventories, schema maps, route maps, or large frontend API type files in full unless debugging that generated artifact directly. Prefer targeted search and regenerated output checks.
- Avoid full `Restore.md` reads except on relaunch or when the latest handoff is specifically needed.
- Avoid dumping full Docker Compose build logs into the conversation unless an issue requires the details. For routine rebuilds, run the build, then use health checks, endpoint smokes, `docker compose ps`, or targeted `docker logs --tail` on failing services.
- For Docker failures, escalate from concise status to targeted logs: first health/status, then the failing service tail, then full logs only when the tail does not identify the issue.
- Keep smoke evidence in docs high-signal: absolute local timestamp, endpoint/path, session or artifact ids, observed status/result, and any relevant blocker. Do not paste full command output.
- If a source file, plan, or doc repeatedly requires long reads to answer narrow questions, treat that as a decomposition smell. Prefer creating or updating a module README, index, contract summary, or generated inventory rather than continuing to rely on large file scans.
