export type FailureKind = "aborted" | "timeout" | "denied" | "unavailable" | "resnapshot" | "invalid_response" | "network";

const messages: Record<FailureKind, string> = {
  aborted: "The request was superseded.", timeout: "The graph read timed out.",
  denied: "This graph is not available to this session.", unavailable: "This graph record is unavailable.",
  resnapshot: "The graph changed. Refresh its snapshot.", invalid_response: "The graph response could not be verified.",
  network: "The graph service could not be reached.",
};

export class ReadFailure extends Error {
  constructor(readonly kind: FailureKind) { super(messages[kind]); this.name = "ReadFailure"; }
}

export function asReadFailure(error: unknown): ReadFailure {
  return error instanceof ReadFailure ? error : new ReadFailure("invalid_response");
}
