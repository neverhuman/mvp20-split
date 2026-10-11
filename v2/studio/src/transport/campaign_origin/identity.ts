import type { CampaignOrigin, OriginDraft } from "../../contracts/campaign_origin.js";
import { active, sha256 } from "../provenance/integrity.js";
import { canonical, requireReply, same } from "../scientific/identity.js";

/** Planning attests its own history; this digest is consistency, not a signature. */
export async function verifyOrigin(value: CampaignOrigin, expected: OriginDraft, signal: AbortSignal) {
  active(signal);
  const origin = value.origin, proposal = origin.proposal, outcome = origin.save.receipt.outcome;
  requireReply(value.schema_version === "2" && origin.schema_version === "2" && same(origin.draft, expected));
  requireReply(await sha256(new TextEncoder().encode(canonical(origin))) === value.origin_sha256);
  active(signal);
  requireReply(same(proposal.attempt.engagement.scope, expected.scope) && same(proposal.context.scope, expected.scope));
  requireReply(outcome.status === "accepted" && outcome.binding.identity.command_family === "definition.save" &&
    same(outcome.binding.identity.scope, expected.scope));
  requireReply(outcome.committed.kind === "draft_revision" && outcome.committed.object_id === expected.draft_id &&
    outcome.committed.revision === expected.revision && outcome.committed.content_sha256 === expected.content_sha256);
  const context = proposal.context;
  const artifacts = [context.objective, context.prompt, context.policy, context.model.configuration,
    ...context.entries.map(item => item.artifact), ...context.omissions.map(item => item.artifact)];
  requireReply(artifacts.every(ref => same(ref.scope, expected.scope)));
  const research = origin.research, selection = research.selection;
  if (!selection) requireReply(research.records.length === 0);
  else {
    requireReply(same(selection.engagement, proposal.attempt.engagement) && selection.request_sha256 === proposal.attempt.request_sha256);
    const identities = new Set([...selection.questions.map(ref => canonical(["question", ref])),
      ...selection.needs.map(ref => canonical(["need", ref])), ...selection.assessments.map(item => canonical(["assessment", item.request]))]);
    requireReply(identities.size === research.records.length);
    for (const row of research.records) {
      requireReply(identities.delete(canonical([row.kind, row.reference])));
      requireReply((row.record_sha256 === null) === (row.unavailable !== null));
      requireReply(new Set(row.criterion_ids).size === row.criterion_ids.length &&
        (!row.criterion_ids.length || row.unavailable === null && row.kind !== "assessment"));
    }
    requireReply(identities.size === 0);
  }
  const knowledge = origin.knowledge;
  if (knowledge) {
    requireReply(same(knowledge.graph.scope, expected.scope));
    if (knowledge.status === "available") {
      requireReply(knowledge.vocabulary !== null && knowledge.policy !== null && knowledge.context_sha256 !== null && knowledge.unavailable === null);
      requireReply([...knowledge.entities, ...knowledge.assertions].every(ref => same(ref.graph, knowledge.graph)));
      if (knowledge.head) requireReply(same(knowledge.head.snapshot.graph, knowledge.graph) &&
        same(knowledge.head.change.graph, knowledge.graph) && knowledge.head.snapshot.revision === knowledge.head.change.position);
      else requireReply(!knowledge.entities.length && !knowledge.assertions.length);
    } else requireReply(knowledge.head === null && knowledge.vocabulary === null && knowledge.policy === null &&
      !knowledge.entities.length && !knowledge.assertions.length && knowledge.context_sha256 === null && knowledge.unavailable !== null);
  }
  active(signal);
}
