import type { ControlEdge, ExecutableScopeV4, Nodes, ValueBinding } from "../../contracts/generated/authoring/save.js";
import type { DraftSession } from "./draft_session.js";
import type { EditorCatalog } from "./editor_catalog.js";
import { SchemaFields } from "./schema_fields.js";

type Node = Nodes[number];
const bindingKey = (tool: { capability_id: string; release: string; contract_version: string; image_sha256: string }) =>
  JSON.stringify([tool.capability_id, tool.release, tool.contract_version, tool.image_sha256]);
const referenceKey = (ref: { schema_id: string; version: string; sha256: string }) => JSON.stringify([ref.schema_id, ref.version, ref.sha256]);

/** Atomic local edits only. The Runtime compiler diagnoses dangling and incompatible bindings. */
export class DraftEdits {
  constructor(readonly session: DraftSession, private readonly catalog: EditorCatalog) {}

  scope(path: readonly string[] = []) { return this.resolve(this.session.snapshot.local.definition.body, path); }

  insert(path: readonly string[], node: Node) {
    this.change(path, scope => {
      if (scope.nodes.some(item => item.node_id === node.node_id)) throw new Error("node_identity_exists");
      scope.nodes.push(structuredClone(node));
    });
  }

  insertTool(path: readonly string[], nodeId: string, descriptor: string) {
    const release = this.catalog.select(descriptor), scope = this.session.snapshot.local.definition.scope;
    if (release.scope.tenant_id !== scope.tenant_id || release.scope.project_id !== scope.project_id) throw new Error("tool_scope_mismatch");
    this.insert(path, { kind: "invoke", node_id: nodeId, tool: release.descriptor.tool.binding,
      inputs: [], timeout_seconds: release.descriptor.resources.timeout_seconds });
  }

  replace(path: readonly string[], id: string, node: Node) {
    if (node.node_id !== id) throw new Error("node_identity_changed");
    this.change(path, scope => { const index = this.index(scope, id); scope.nodes[index] = structuredClone(node); });
  }

  remove(path: readonly string[], id: string) {
    // Deliberately retain incident edges and consumers. A deletion is not authority to rewrite dependencies.
    this.change(path, scope => { scope.nodes.splice(this.index(scope, id), 1); });
  }

  connect(path: readonly string[], edge: ControlEdge) {
    this.change(path, scope => {
      this.index(scope, edge.source); this.index(scope, edge.target);
      const edges = scope.edges ?? [];
      if (edges.some(item => item.source === edge.source && item.target === edge.target && (item.route ?? "next") === (edge.route ?? "next")))
        throw new Error("edge_exists");
      scope.edges = [...edges, structuredClone(edge)];
    });
  }

  disconnect(path: readonly string[], index: number) {
    this.change(path, scope => {
      if (!Number.isSafeInteger(index) || index < 0 || index >= (scope.edges?.length ?? 0)) throw new Error("edge_not_found");
      scope.edges!.splice(index, 1);
    });
  }

  bindInput(path: readonly string[], id: string, port: string, source: ValueBinding["source"] | null) {
    this.change(path, scope => {
      const node = scope.nodes[this.index(scope, id)]!;
      if (node.kind !== "invoke") throw new Error("invoke_required");
      const choice = this.catalog.snapshot.choices?.find(item => bindingKey(item.release.lock.tool) === bindingKey(node.tool));
      if (!choice) throw new Error("tool_metadata_unavailable");
      const release = this.catalog.select(choice.release.lock.descriptor_sha256);
      if (!release.descriptor.tool.inputs.some(item => item.name === port)) throw new Error("input_port_unknown");
      if (node.inputs.filter(item => item.port === port).length > 1) throw new Error("input_port_ambiguous");
      node.inputs = node.inputs.filter(item => item.port !== port);
      if (source !== null) node.inputs.push({ port, source: structuredClone(source) });
    });
  }

  parameterNode(path: readonly string[], invokeId: string, port: string, nodeId: string) {
    this.change(path, scope => {
      if (scope.nodes.some(node => node.node_id === nodeId)) throw new Error("node_identity_exists");
      const invoke = scope.nodes[this.index(scope, invokeId)]!;
      if (invoke.kind !== "invoke") throw new Error("invoke_required");
      const choice = this.catalog.snapshot.choices?.find(item => bindingKey(item.release.lock.tool) === bindingKey(invoke.tool));
      if (!choice) throw new Error("tool_metadata_unavailable");
      const release = this.catalog.select(choice.release.lock.descriptor_sha256), input = release.descriptor.tool.inputs.find(item => item.name === port);
      if (!input) throw new Error("input_port_unknown");
      if (invoke.inputs.some(item => item.port === port)) throw new Error("input_already_bound");
      scope.nodes.push({ kind: "artifact_materialize", node_id: nodeId, fields: [], output: { name: "value", value_type: {
        kind: "artifact", representation: input.representation, unit: input.unit, schema_ref: input.schema_ref,
      } } });
      invoke.inputs.push({ port, source: { kind: "output", node_id: nodeId, port: "value" } });
      scope.edges = [...scope.edges ?? [], { source: nodeId, target: invokeId, route: "next" }];
    });
  }

  materializedConstant(path: readonly string[], id: string, name: string, text: string) {
    this.change(path, scope => {
      const node = scope.nodes[this.index(scope, id)]!, catalog = this.catalog.snapshot;
      if (node.kind !== "artifact_materialize" || node.output.value_type.kind !== "artifact") throw new Error("materializer_required");
      if (catalog.phase !== "ready" || catalog.schemaPhase !== "ready" || !catalog.schema ||
          referenceKey(catalog.schema.reference) !== referenceKey(node.output.value_type.schema_ref)) throw new Error("reviewed_output_schema_required");
      const source = new SchemaFields(catalog.schema.document).constant(name, text);
      if (node.fields.filter(field => field.name === name).length > 1) throw new Error("materializer_field_ambiguous");
      node.fields = [...node.fields.filter(field => field.name !== name), { name, mode: "inline", source }];
    });
  }

  private change(path: readonly string[], edit: (scope: ExecutableScopeV4) => void) {
    const local = this.session.snapshot.local;
    edit(this.resolve(local.definition.body, path));
    this.session.edit(local);
  }
  private index(scope: ExecutableScopeV4, id: string) {
    const matches = scope.nodes.flatMap((node, index) => node.node_id === id ? [index] : []);
    if (matches.length !== 1) throw new Error(matches.length ? "node_identity_ambiguous" : "node_not_found");
    return matches[0]!;
  }
  private resolve(root: ExecutableScopeV4, path: readonly string[]) {
    if (path.length > 32) throw new Error("scope_path_too_deep");
    let scope = root;
    for (const id of path) {
      const node = scope.nodes[this.index(scope, id)]!;
      if (node.kind !== "iterate" && node.kind !== "scatter") throw new Error("scope_node_required");
      scope = node.body;
    }
    return scope;
  }
}
