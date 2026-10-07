import type { ValidateFunction } from "ajv";
import compiled from "./generated/validators.js";
import type { GraphSnapshotPage } from "./generated/snapshot.js";
import type { GraphNodeDetail } from "./generated/detail.js";
import type { GraphValuePage } from "./generated/values.js";
import type { GraphInvalidationPage } from "./generated/events.js";
import type { GraphScopePage } from "./generated/scopes.js";
import type { GraphTopologyPage } from "./generated/topology.js";
import type { GraphViewCatalog } from "./generated/catalog.js";
import type { SuccessorLineage } from "./generated/lineage.js";
import type { CompletionRecord } from "./generated/completion.js";
import type { ArtifactRef } from "./generated/artifact.js";

export type { GraphSnapshotPage, GraphNodeDetail, GraphValuePage, GraphInvalidationPage, GraphScopePage, GraphTopologyPage };
export type { GraphViewCatalog, SuccessorLineage };
export type { CompletionRecord, ArtifactRef };
export type TopologyQuery = GraphTopologyPage["query"];
export type ReadCut = GraphSnapshotPage["snapshot"]["cut"];
export type ReadQuery = GraphSnapshotPage["snapshot"]["query"];
export type GraphNode = GraphSnapshotPage["nodes"][number];
export interface ObservationWire {
  snapshot: GraphSnapshotPage;
  detail: GraphNodeDetail;
  values: GraphValuePage;
  events: GraphInvalidationPage;
  scopes: GraphScopePage;
  topology: GraphTopologyPage;
  catalog: GraphViewCatalog;
  lineage: SuccessorLineage;
  completion: CompletionRecord;
  artifact: ArtifactRef;
}

const validators = compiled as Record<string, ValidateFunction>;

export function decodeObservation<K extends keyof ObservationWire>(kind: K, value: unknown): ObservationWire[K] {
  const validate = validators[kind] as ValidateFunction<ObservationWire[K]>;
  if (!validate(value)) throw new Error("invalid_observation_response");
  return value;
}
