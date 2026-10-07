import type { ValidateFunction } from "ajv";
import validators from "./generated/followup/validators.js";
import pins from "./generated/followup/profiles.json" with { type: "json" };
import type { CheckpointFollowupDraft } from "./generated/followup/followup.js";
import type { CheckpointDraft } from "./generated/followup/checkpoint.js";
import type { CampaignDraft } from "./generated/followup/campaign.js";
import type { SupervisionResponse } from "./generated/followup/response.js";
import { same } from "../transport/scientific/identity.js";

export type { CheckpointFollowupDraft, SupervisionResponse };
export type CriterionRef = CheckpointFollowupDraft["unresolved"][number]["criterion"];
export type ProposalDocument = { readonly kind: "followup"; readonly draft: CheckpointFollowupDraft } |
  { readonly kind: "checkpoint"; readonly draft: CheckpointDraft } | { readonly kind: "campaign"; readonly draft: CampaignDraft };
interface Wires { followup: CheckpointFollowupDraft; checkpoint: CheckpointDraft; campaign: CampaignDraft; response: SupervisionResponse }
export function decodeFollowup<K extends keyof Wires>(kind: K, value: unknown): Wires[K] {
  const check = (validators as Record<string, ValidateFunction>)[kind] as ValidateFunction<Wires[K]>;
  if (!check(value)) throw new Error("invalid_followup_record");
  return value;
}
export function proposalProfile(profile: NonNullable<SupervisionResponse["observation"]["proposal"]>["output_schema"]): ProposalDocument["kind"] | null {
  for (const kind of ["followup", "checkpoint", "campaign"] as const) if (same(profile, pins[kind])) return kind;
  return null;
}
export function decodeProposal(kind: ProposalDocument["kind"], value: unknown): ProposalDocument {
  if (kind === "followup") return { kind, draft: decodeFollowup(kind, value) };
  if (kind === "checkpoint") return { kind, draft: decodeFollowup(kind, value) };
  return { kind, draft: decodeFollowup(kind, value) };
}
