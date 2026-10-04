import { decodeProvenance, decodeMaterialStateRevisionRef, decodeExperimentRevisionRef, decodeObservationRevisionRef, decodeResearchQuestionRef, decodeEvidenceNeedRef } from "../../contracts/scientific/provenance.js";
import type { MaterialStateRevision, ExperimentDefinition, ObservationRevision, ResearchQuestion, EvidenceNeed, InterpretationRef } from "../../contracts/scientific/provenance.js";
import { ScientificHTTP } from "../scientific/http.js";
import { ScientificReadFailure } from "../scientific/failure.js";
import { normalized, requireReply, same } from "../scientific/identity.js";

const base = "/api/research/v1/";

export class ResearchRecordClient {
  private readonly http: ScientificHTTP;
  constructor(fetcher: typeof fetch = fetch, timeoutMs = 15_000) { this.http = new ScientificHTTP(fetcher, timeoutMs); }

  private async exact<R extends object, T extends { reference: object }>(path: string, reference: R, check: (value: unknown) => R, decode: (value: unknown) => T, signal: AbortSignal): Promise<T> {
    const expected = normalized(reference, {}, check);
    const result = await this.http.post(base + path + "/read", expected, decode, signal);
    requireReply(same(result.reference, expected));
    return result;
  }

  material(reference: MaterialStateRevision["reference"], signal: AbortSignal) {
    return this.exact("material-states", reference, decodeMaterialStateRevisionRef, value => decodeProvenance("material", value), signal);
  }
  experiment(reference: ExperimentDefinition["reference"], signal: AbortSignal) {
    return this.exact("experiments", reference, decodeExperimentRevisionRef, value => decodeProvenance("experiment", value), signal);
  }
  observation(reference: ObservationRevision["reference"], signal: AbortSignal) {
    return this.exact("observations", reference, decodeObservationRevisionRef, value => decodeProvenance("observation", value), signal);
  }
  question(reference: ResearchQuestion["reference"], signal: AbortSignal) {
    return this.exact("questions", reference, decodeResearchQuestionRef, value => decodeProvenance("question", value), signal);
  }
  need(reference: EvidenceNeed["reference"], signal: AbortSignal) {
    return this.exact("evidence-needs", reference, decodeEvidenceNeedRef, value => decodeProvenance("need", value), signal);
  }

  async interpretation(reference: InterpretationRef, signal: AbortSignal) {
    const expected = normalized(reference, {}, value => decodeProvenance("interpretation_ref", value));
    const selection = { scope: expected.scope, kind: expected.kind, interpretation_id: expected.interpretation_id };
    const result = await this.http.post(base + "observation-interpretations/read", selection, value => decodeProvenance("interpretation", value), signal);
    requireReply(result.request.kind === expected.kind && result.request.interpretation_id === expected.interpretation_id && same(result.request.profile.scope, expected.scope));
    if (result.outcome.status === "pending") throw new ScientificReadFailure("unavailable");
    requireReply(same(result.outcome.projection.reference, expected) && result.outcome.projection.actor_id === result.actor_id);
    return result;
  }

  async observationCorrection(reference: ObservationRevision["reference"], signal: AbortSignal) {
    const expected = normalized(reference, {}, decodeObservationRevisionRef);
    const result = await this.http.post(base + "observation-corrections/read", expected, value => decodeProvenance("observation_correction", value), signal);
    requireReply(same(result.after.reference, expected) && same(result.after.supersedes, result.before.reference));
    requireReply(same(result.before.reference.scope, expected.scope) && result.before.reference.observation_id === expected.observation_id && result.before.reference.revision + 1 === expected.revision);
    return result;
  }

  async materialCorrection(reference: MaterialStateRevision["reference"], signal: AbortSignal) {
    const expected = normalized(reference, {}, decodeMaterialStateRevisionRef);
    const result = await this.http.post(base + "material-state-corrections/read", expected, value => decodeProvenance("material_correction", value), signal);
    requireReply(same(result.after.reference, expected) && same(result.after.supersedes, result.before.reference));
    requireReply(same(result.before.reference.scope, expected.scope) && result.before.reference.material_state_id === expected.material_state_id && result.before.reference.revision + 1 === expected.revision);
    return result;
  }
}
