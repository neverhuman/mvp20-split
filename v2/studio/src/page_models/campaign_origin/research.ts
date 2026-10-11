import type { OriginBody, OriginResearchRecord } from "../../contracts/campaign_origin.js";
import type { ResearchQuestion, EvidenceNeed } from "../../contracts/scientific/provenance.js";
import type { ResearchRecordClient } from "../../transport/provenance/research.js";
import { active, sha256 } from "../../transport/provenance/integrity.js";
import { canonical, requireReply, same } from "../../transport/scientific/identity.js";
import { ScientificReadFailure } from "../../transport/scientific/failure.js";

export interface OriginCriteria { question: ResearchQuestion; need: EvidenceNeed | null }

export class OriginResearchReader {
  constructor(private readonly source: Pick<ResearchRecordClient, "question" | "need">) {}
  private async question(row: OriginResearchRecord, signal: AbortSignal) {
    requireReply(row.kind === "question" && "question_id" in row.reference && row.record_sha256 !== null);
    const question = await this.source.question(row.reference, signal);
    active(signal);
    requireReply(same(question.reference, row.reference) &&
      await sha256(new TextEncoder().encode(canonical(question))) === row.record_sha256 &&
      same(question.criteria.map(criterion => criterion.criterion_id), row.criterion_ids));
    active(signal); return question;
  }
  async read(origin: OriginBody, index: number, signal: AbortSignal): Promise<OriginCriteria> {
    const row = origin.research.records[index];
    requireReply(Number.isSafeInteger(index) && !!row && row.unavailable === null);
    if (row.kind === "question") return { question: await this.question(row, signal), need: null };
    requireReply(row.kind === "need" && "need_id" in row.reference && row.record_sha256 !== null);
    const need = await this.source.need(row.reference, signal);
    active(signal);
    requireReply(same(need.reference, row.reference) && same(need.criterion_ids, row.criterion_ids) &&
      await sha256(new TextEncoder().encode(canonical(need))) === row.record_sha256);
    const questionRow = origin.research.records.find(record => record.kind === "question" && same(record.reference, need.question));
    if (!questionRow || questionRow.unavailable !== null) throw new ScientificReadFailure("unavailable");
    const question = await this.question(questionRow, signal);
    requireReply(need.criterion_ids.every(id => question.criteria.some(criterion => criterion.criterion_id === id)));
    active(signal); return { question, need };
  }
}
