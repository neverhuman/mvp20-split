import { Ajv2020 } from "ajv/dist/2020.js";
import type { ValidateFunction } from "ajv";
import addFormats from "ajv-formats";
import schemas from "./generated/schemas.json" with { type: "json" };
import type { GraphSnapshotPage } from "./generated/snapshot.js";
import type { GraphNodeDetail } from "./generated/detail.js";
import type { GraphValuePage } from "./generated/values.js";
import type { GraphInvalidationPage } from "./generated/events.js";
import type { GraphScopePage } from "./generated/scopes.js";
import type { GraphTopologyPage } from "./generated/topology.js";

export type { GraphSnapshotPage, GraphNodeDetail, GraphValuePage, GraphInvalidationPage, GraphScopePage, GraphTopologyPage };
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
}

const ajv = new Ajv2020({ strict: true, allErrors: false, coerceTypes: false, useDefaults: false, removeAdditional: false });
// Pydantic's OpenAPI discriminator is an annotation; JSON Schema oneOf/const enforces the union.
ajv.addKeyword({ keyword: "discriminator", schemaType: "object", valid: true });
addFormats.default(ajv);
const validators = {
  snapshot: ajv.compile<GraphSnapshotPage>(schemas.snapshot),
  detail: ajv.compile<GraphNodeDetail>(schemas.detail),
  values: ajv.compile<GraphValuePage>(schemas.values),
  events: ajv.compile<GraphInvalidationPage>(schemas.events),
  scopes: ajv.compile<GraphScopePage>(schemas.scopes),
  topology: ajv.compile<GraphTopologyPage>(schemas.topology),
};

export function decodeObservation<K extends keyof ObservationWire>(kind: K, value: unknown): ObservationWire[K] {
  const validate = validators[kind] as ValidateFunction<ObservationWire[K]>;
  if (!validate(value)) throw new Error("invalid_observation_response");
  return value;
}
