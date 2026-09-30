import { useEffect, useState } from "react";
import type { Nodes, ValueBinding } from "../contracts/generated/authoring/save.js";
import type { DraftEdits } from "../page_models/design/draft_edits.js";
import type { EditorCatalog } from "../page_models/design/editor_catalog.js";
import { SchemaFields } from "../page_models/design/schema_fields.js";
import type { SchemaField } from "../page_models/design/schema_fields.js";
import { parseDraftJSON } from "../page_models/design/scalar_input.js";

type Action = (action: () => void) => void;
type Node = Nodes[number];
function ScalarEditor({ field, value, apply, disabled }: { field: SchemaField; value: unknown; apply: (text: string) => void; disabled: boolean }) {
  const initial = value ?? field.fixed;
  const [text, setText] = useState(initial === undefined ? "" : String(initial));
  return <div className="draft-field"><label>{field.name}{field.required ? " (required)" : ""}
    {field.kind === "boolean" || field.choices ? <select aria-label={field.name + (field.required ? " (required)" : "")} disabled={disabled} value={text} onChange={event => setText(event.target.value)}>
      <option value="">Choose a value</option>{(field.choices ?? [true, false]).map(item => <option key={String(item)} value={String(item)}>{String(item)}</option>)}
    </select> : <input disabled={disabled} value={text} maxLength={field.kind === "string" ? 4096 : 512} onChange={event => setText(event.target.value)} />}</label>
    <button disabled={disabled} onClick={() => apply(text)}>Apply {field.name}</button><p>Applied value: {value === undefined ? "Unbound" : String(value)}</p></div>;
}

function InputBinding({ name, source, apply, disabled }: { name: string; source: ValueBinding["source"] | undefined; apply: (source: ValueBinding["source"] | null) => void; disabled: boolean }) {
  const [kind, setKind] = useState<"input" | "output">(source?.kind === "output" ? "output" : "input");
  const [origin, setOrigin] = useState(source?.kind === "output" ? source.node_id : source?.kind === "input" ? source.name : "");
  const [port, setPort] = useState(source?.kind === "output" ? source.port : "");
  return <fieldset disabled={disabled}><legend>{name}</legend>
    <p>Current binding: {source ? JSON.stringify(source) : "Unbound"}</p>
    <label>Source type<select aria-label="Source type" value={kind} onChange={event => setKind(event.target.value as "input" | "output")}><option value="input">Scope input</option><option value="output">Node output</option></select></label>
    <label>{kind === "input" ? "Input name" : "Source node"}<input maxLength={128} value={origin} onChange={event => setOrigin(event.target.value)} /></label>
    {kind === "output" && <label>Output port<input maxLength={128} value={port} onChange={event => setPort(event.target.value)} /></label>}
    <button onClick={() => apply(kind === "input" ? { kind, name: origin } : { kind, node_id: origin, port })}>Apply {name} binding</button>
    <button onClick={() => apply(null)}>Clear {name} binding</button>
  </fieldset>;
}

export function DraftInspector({ node, edits, path, catalog, perform, openScope, selectNode, disabled }: {
  node: Node; edits: DraftEdits; path: string[]; catalog: EditorCatalog; perform: Action; openScope: () => void; selectNode: (id: string) => void; disabled: boolean;
}) {
  const [raw, setRaw] = useState(JSON.stringify(node, null, 2));
  const [rawBase, setRawBase] = useState(JSON.stringify(node, null, 2));
  const [parameterId, setParameterId] = useState("parameters");
  const currentRaw = JSON.stringify(node, null, 2), rawStale = currentRaw !== rawBase && raw !== rawBase;
  useEffect(() => { if (raw === rawBase && currentRaw !== rawBase) { setRaw(currentRaw); setRawBase(currentRaw); } }, [currentRaw, raw, rawBase]);
  const view = catalog.snapshot;
  const release = node.kind === "invoke" ? view.choices?.find(choice => {
    const binding = choice.release.lock.tool;
    return binding.capability_id === node.tool.capability_id && binding.release === node.tool.release && binding.image_sha256 === node.tool.image_sha256 && binding.contract_version === node.tool.contract_version;
  }) : undefined;
  const materializer = node.kind === "artifact_materialize" && node.output.value_type.kind === "artifact" ? node.output.value_type : undefined;
  const schema = materializer && view.schemaPhase === "ready" && view.schema &&
    view.schema.reference.sha256 === materializer.schema_ref.sha256 && view.schema.reference.schema_id === materializer.schema_ref.schema_id &&
    view.schema.reference.version === materializer.schema_ref.version ? new SchemaFields(view.schema.document) : undefined;
  return <section aria-label="Draft node inspector" className="draft-inspector">
    <h2>{node.node_id}</h2><p>{node.kind} · Next-campaign draft</p>
    {(node.kind === "iterate" || node.kind === "scatter") && <button onClick={openScope}>Open nested scope</button>}
    {node.kind === "invoke" && <>
      <p>{release?.release.descriptor.tool.purpose ?? "Reviewed tool metadata is unavailable on this catalog page."}</p>
      <p>Execution eligibility and scientific applicability are not established.</p>
      <label>Parameter node ID<input value={parameterId} onChange={event => setParameterId(event.target.value)} maxLength={128} disabled={disabled} /></label>
      {release?.release.descriptor.tool.inputs.map(input => <div key={input.name}>
        <p>{input.name} · {input.representation} · {input.unit}{input.required !== false ? " · required" : ""}</p>
        <InputBinding key={JSON.stringify(node.inputs.find(binding => binding.port === input.name)) + input.name} name={input.name}
          source={node.inputs.find(binding => binding.port === input.name)?.source} disabled={disabled || view.phase !== "ready" || !release.authoringAvailable}
          apply={source => perform(() => edits.bindInput(path, node.node_id, input.name, source))} />
        <button disabled={view.phase !== "ready"} onClick={() => void catalog.inspectSchema(input.schema_ref)}>Inspect {input.name} schema</button>
        <button disabled={disabled || view.phase !== "ready" || !release.authoringAvailable || node.inputs.some(binding => binding.port === input.name)}
          onClick={() => perform(() => { edits.parameterNode(path, node.node_id, input.name, parameterId); selectNode(parameterId); })}>Create parameter node for {input.name}</button>
      </div>)}
      {view.schemaPhase === "ready" && view.schema && <details><summary>Reviewed schema</summary><pre>{JSON.stringify(view.schema.document, null, 2)}</pre></details>}
    </>}
    {materializer && <>
      <button disabled={view.phase !== "ready"} onClick={() => void catalog.inspectSchema(materializer.schema_ref)}>Load parameter fields</button>
      {schema?.unavailable && <p>{schema.unavailable}</p>}
      {schema?.snapshot.fields.map(field => {
        const current = node.kind === "artifact_materialize" ? node.fields.find(item => item.name === field.name)?.source : undefined;
        return field.kind === "binding" ? <p key={field.name}>{field.name}: {field.reason}</p> : <ScalarEditor key={field.name} field={field}
          value={current && "value" in current ? current.value : undefined} disabled={disabled || view.phase !== "ready"}
          apply={text => perform(() => edits.materializedConstant(path, node.node_id, field.name, text))} />;
      })}
    </>}
    {view.schemaPhase === "loading" && <p role="status">Loading exact reviewed schema…</p>}
    {view.schemaPhase === "unavailable" && <p role="status">Schema unavailable. Existing draft content is retained.</p>}
    <details><summary>Advanced node definition</summary><p>All executable primitives are available here. Validation checks the complete graph.</p>
      <label>Node JSON<textarea aria-label="Node JSON" value={raw} onChange={event => setRaw(event.target.value)} maxLength={262144} rows={16} disabled={disabled} /></label>
      {rawStale && <p>The node changed after this source edit began. Copy your source changes before reloading the current node.</p>}
      <button disabled={disabled || rawStale} onClick={() => perform(() => { edits.replace(path, node.node_id, parseDraftJSON(raw) as Node); setRawBase(raw); })}>Apply node definition</button>
      <button disabled={disabled} onClick={() => { setRaw(currentRaw); setRawBase(currentRaw); }}>Reload node source</button>
    </details>
    <button disabled={disabled} onClick={() => perform(() => edits.remove(path, node.node_id))}>Remove node</button>
    <p>Removal retains dependent bindings for explicit repair and validation.</p>
  </section>;
}
