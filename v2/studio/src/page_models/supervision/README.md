# Supervisor inspection model

Owner: Studio,BP-07.05/B1.04.

SupervisionModel owns a single selection-driven region: checkpoint list,request list,context or responses. Each page replaces the last; no unbounded client cache. RequestLane cancels and fences old replies across selection,refresh,scope/run binding,hidden-view invalidation and disposal. Refresh preserves selected checkpoint/request and restarts pagination against a fresh snapshot. Denial clears retained displayed metadata. Outcome is an independent exact Runtime read; unavailable outcome explicitly marks partial evidence rather than inferring pending. No run mutations or scientific quality authority. Owned tests: tests/page_models/supervision.test.ts.

Replacement must preserve public wire contracts,scope isolation,coherent page boundaries and truthful states. Python supervision schemas remain authoritative.

SQ-01/B3: optional FollowupModel and CriterionModel are lifecycle-owned children.
inspectResponse accepts only a response ID from the current ready response page.
Every publish, rebind, invalidation and dispose clears both; disposal disposes them.
No new content read is performed when children are absent.
