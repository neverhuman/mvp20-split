export type ScientificFailureKind = "aborted" | "timeout" | "denied" | "unavailable" | "query_conflict" | "invalid_request" | "invalid_response" | "limit" | "network";
const messages: Record<ScientificFailureKind, string> = {
  aborted: "This read was superseded.", timeout: "The evidence read timed out.",
  denied: "This evidence is not available to this session.", unavailable: "The selected evidence is unavailable.",
  query_conflict: "This selection does not match its continuation.", invalid_request: "The evidence selection is invalid.",
  invalid_response: "The evidence response could not be verified.", limit: "This selection exceeds the supported read limit.",
  network: "The evidence service could not be reached.",
};
export class ScientificReadFailure extends Error {
  constructor(readonly kind: ScientificFailureKind) { super(messages[kind]); this.name = "ScientificReadFailure"; }
}
