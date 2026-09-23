# Agent Work and Supervision

- Design status: detailed proposed contract; implementation and scientific acceptance pending
- Naming note: component/record/operation names below are proposed logical design, not implemented APIs or selected deployment technology
- Last reviewed: `2026-09-22 18:56:40` (America/Chicago)
- Parent: [Domain overview](Agent_Architecture.md)
- Requirement source: [Product Requirements](../Product_Requirements.md#fully-agent-orchestrated-and-supported-environment)

## Owned Contract

Durable tasks bind objective, requester, scope, agent version, dependencies, inputs, grants, budget, deadline, checkpoints, approvals, outputs and disposition. Separate proposal, execution and review roles. Campaign tasks bind canonical run/node identities; no hidden competing execution topology is allowed.

Represent dependency/approval/customer waits, retryable failure, blocked, cancelled, superseded and complete states explicitly. Reuse Campaigns/Platform lease, heartbeat, retry, cancellation and compensation mechanisms. Handoffs preserve exact continuation state and missing authority.

## Control and Lifecycle

Initial internal/demo campaigns are fully autonomous: eligible agents and deterministic policies conduct required reviews within configured authority. Routine human approval waits are not part of this profile. Unresolvable gaps yield a terminal blocked/abstained outcome with next-campaign proposals. Human feedback changes the next campaign; emergency termination and revocation remain operational controls. General human-wait capabilities below are future-profile support, not initial acceptance requirements.

Least-privilege grants and evaluated prompt/tool/workflow versions bound actions. Standing approvals permit scoped routine work; material effects stop at named gates. Emergency stops reconcile in-flight effects. Evaluation, shadow/limited-active promotion, quarantine and rollback preserve history.

## Invariants and Verification

No authority expansion to finish work or approval laundering through consensus/decomposition. Verify restart, dependencies/provider failure, duplication, intervention and separation of duties. Assess correctness, grounding, abstention, escalation, privacy, cost and recovery, not task completion alone. Support agents expose only authorized status.

## Component and Object Design

| Proposed component | Authoritative ownership |
|---|---|
| Agent registry | Role/profile/version, capabilities, quality evidence and lifecycle |
| Task aggregate | Objective, grants, dependencies, current disposition and campaign binding |
| Assignment coordinator | Eligible agent selection and binding to runtime attempts |
| Supervision policy | Budget/deadline checks, waiting/escalation and intervention disposition |
| Support/handoff assembler | Scoped continuation packets and incident references |

`AgentTask` is not another campaign graph. Campaign-bound tasks reference run/node identity; independent support tasks have durable work records and policy-controlled execution without becoming scientific campaign topology. Authoritative completion and attempt fencing are supplied by the execution mechanism, not inferred from a conversation message.

## Work and Supervision Flow

Accept a scoped objective, resolve eligible profile/grants, bind dependencies and dispatch through the execution contract. Progress messages update observations, while committed results establish task disposition. Waiting states name the missing prerequisite or approver and exact continuation inputs. Approval expiry or revocation requires renewed eligibility at the effect boundary.

An intervention may pause future dispatch, cancel work, request clarification or propose reassignment. Record who acted, which task revision was targeted, the impact on running effects and the safe continuation point. Reassignment cannot widen scientific/data permissions.

## Failure and Boundary Example

An agent reports success after its grant expired or attempt lease was replaced. Treat its output as unaccepted evidence pending validation; do not let the message overwrite the current task. A support agent may explain a withheld result using authorized status metadata without exposing the rejected private payload.

## Design Basis and Open Decisions

The agent-orchestration requirements supply task and supervision contracts. Remaining decisions: role inventory, task-to-runtime mapping for noncampaign work, routing quality and evaluation thresholds. Shared durable mechanisms may be reused; independent hidden queues with conflicting completion state are not acceptable.
