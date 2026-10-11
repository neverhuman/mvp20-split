import type { ArtifactRef, GraphSnapshotPage } from "../../contracts/observations.js";
import { decodeAuthoring } from "../../contracts/authoring.js";
import type { LaunchReceipt } from "../../contracts/launch.js";
import type { AuthoringClient } from "../../transport/authoring.js";
import type { LaunchSubmission } from "../../transport/launch/submission.js";
import { same } from "../../transport/scientific/identity.js";
import { isCampaignContext } from "../campaign_flow/context.js";

/** A launch-bound planning artifact is context before it becomes a retained finish output. */
export class LaunchPlanningContext {
  private readonly receipt: LaunchReceipt;
  constructor(private readonly command: LaunchSubmission, receipt: LaunchReceipt, private readonly source: Pick<AuthoringClient, "draft">) {
    this.receipt = command.verify(receipt);
    if (!this.receipt.run_id) throw Error("admission_required");
  }
  selection(snapshot: GraphSnapshotPage["snapshot"]) {
    const request = this.command.request, admission = request.payload.admission.payload, draft = admission.draft;
    if (snapshot.cut.run_id !== this.receipt.run_id || !same(snapshot.cut.scope, request.identity.scope) ||
      snapshot.cut.plan_sha256 !== admission.plan_sha256) throw Error("launch_observation_mismatch");
    return { scope: structuredClone(request.identity.scope), draft_id: draft.draft_id,
      revision: draft.revision, content_sha256: draft.content_sha256 };
  }
  async reference(snapshot: GraphSnapshotPage["snapshot"], signal: AbortSignal): Promise<ArtifactRef | null> {
    const request = this.command.request, admission = request.payload.admission.payload, selection = this.selection(snapshot);
    const draft = decodeAuthoring("draft", await this.source.draft(selection.draft_id, selection.revision, signal));
    if (!same(draft.scope, request.identity.scope) || draft.head.draft_id !== selection.draft_id ||
      draft.head.revision !== selection.revision || draft.head.content_sha256 !== selection.content_sha256) throw Error("launch_draft_mismatch");
    const refs: ArtifactRef[] = [];
    for (const node of draft.definition.body.nodes) {
      if (node.kind !== "finish") continue;
      for (const output of node.outputs) {
        const source = output.source;
        const value = source.kind === "input" ? admission.inputs.find(input => input.port === source.name)?.value : source;
        if (value?.kind === "artifact" && isCampaignContext(value.artifact)) refs.push(value.artifact);
      }
    }
    if (refs.length > 1) throw Error("launch_context_ambiguous");
    return refs[0] ?? null;
  }
}
