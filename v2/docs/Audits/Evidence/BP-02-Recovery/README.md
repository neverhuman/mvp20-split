# BP-02 Recovery Evidence

These nine credential-free manifests preserve the installed acceptance run for scope `integrated-acceptance / 2117ae051f9449f68a2fefc8c9324f98`, recorded on 2026-09-28. Each envelope's SHA-256 covers its canonical sorted compact JSON manifest, including exact public identities, wheel hashes, barriers, owned killed PIDs, restart steps, deadline and observations. Temporary fixture service URLs, database credentials and bearer tokens are absent.

| Case | Independent observation |
|---|---|
| [REC-01](REC-01.json) | Synced bytes cannot publish before selected-attempt commit; retry yields one readable identity |
| [REC-02](REC-02.json) | Finalization receipt and bytes survive process death before response |
| [REC-03](REC-03.json) | PREPARED protection survives runtime outage; replay accepts once |
| [REC-04](REC-04.json) | Accepted completion survives restart before retention confirmation |
| [REC-05](REC-05.json) | Abort/release precedes stale completion; acceptance cannot revive |
| [REC-06](REC-06.json) | Killed worker reclaims under a higher fence; stale completion denied; spending conserved |
| [REC-07](REC-07.json) | Real peer effect before lost ack replays the same operation under a successor delivery generation |
| [REC-08](REC-08.json) | Independent branch completion and paused work survive runtime restart |
| [REC-09](REC-09.json) | Fresh wheel-only service replacements preserve retained state and finish pending retention |

The harness is owned by [runtime acceptance](../../../../services/campaign_runtime/tests/acceptance/README.md). Reproduce with the explicit disposable PostgreSQL fixture and `v2/dev/verify_foundation.py --builds`; new runs produce new scope/identity/timestamp/hash manifests. This is synthetic application process evidence, not scientific efficacy, host power-loss or backup-restore evidence.
