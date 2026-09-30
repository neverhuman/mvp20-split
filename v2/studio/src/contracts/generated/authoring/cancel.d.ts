/* Generated from the published Python-owned serialization schema. Do not edit. */

export type ExpectedRunRevision = number | null;
export type ReasonCode = string;
export type RunId = string;

export interface CancelRun {
  expected_run_revision?: ExpectedRunRevision;
  reason_code: ReasonCode;
  run_id: RunId;
}
