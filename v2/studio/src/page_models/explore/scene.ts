import type { GraphNeighborhoodPage } from "../../contracts/scientific/knowledge.js";
import type { SceneNode, SceneEdge } from "../scene.js";

export const entityKey = (reference: { entity_id: string; revision: number }) => `${reference.entity_id}@${reference.revision}`;

/** Layout is local; only explicit assertions between returned exact endpoints form edges. */
export function domainScene(page: GraphNeighborhoodPage) {
  const nodes: SceneNode[] = page.entities.map((entity, index) => ({ id: entityKey(entity.reference), label: entity.label,
    status: entity.entity_type, x: (index % 3) * 450, y: 100 + Math.floor(index / 3) * 140 }));
  const ids = new Set(nodes.map(node => node.id));
  const edges: SceneEdge[] = page.assertions.filter(assertion => ids.has(entityKey(assertion.subject)) && ids.has(entityKey(assertion.object)))
    .map(assertion => ({ id: `${assertion.reference.assertion_id}@${assertion.reference.revision}`, source: entityKey(assertion.subject),
      target: entityKey(assertion.object), label: `${assertion.predicate.replaceAll("_", " ")} (${assertion.polarity})` }));
  return { nodes, edges, omittedEntities: page.entity_total - nodes.length, omittedAssertions: page.assertion_total - edges.length };
}
