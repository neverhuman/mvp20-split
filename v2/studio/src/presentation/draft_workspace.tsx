import { useCallback, useEffect, useMemo, useState } from "react";
import type { DraftCommands } from "../page_models/design/draft_commands.js";
import type { EditorCatalog } from "../page_models/design/editor_catalog.js";
import { DraftEdits } from "../page_models/design/draft_edits.js";
import { DraftComparison } from "../page_models/design/draft_comparison.js";
import type { ControlEdge, ExecutableScopeV4 } from "../contracts/generated/authoring/save.js";
import { parseDraftJSON } from "../page_models/design/scalar_input.js";
import { GraphCanvas } from "./graph_canvas.js";
import { DraftInspector } from "./draft_inspector.js";
import { DraftComparisonView } from "./draft_comparison.js";
import "./style.css";

/** Host owns the selected scoped session; components never call Runtime or Registry directly. */
export function DraftWorkspace({ commands, catalog, synthetic = false }: { commands: DraftCommands; catalog: EditorCatalog; synthetic?: boolean }) {
  const identity = useMemo(() => crypto.randomUUID(), [commands, catalog]);
  return <BoundDraftWorkspace key={identity} commands={commands} catalog={catalog} synthetic={synthetic} />;
}

function BoundDraftWorkspace({ commands, catalog, synthetic }: { commands: DraftCommands; catalog: EditorCatalog; synthetic: boolean }) {
  const [, render] = useState(0), refresh = useCallback(() => render(value => value + 1), []);
  const [path, setPath] = useState<string[]>([]), [selected, select] = useState<string | null>(null);
  const [nodeId, setNodeId] = useState("new-node"), [descriptor, setDescriptor] = useState("");
  const [error, setError] = useState<string | null>(null), [compare, setCompare] = useState(false);
  const [edgeSource, setEdgeSource] = useState(""), [edgeTarget, setEdgeTarget] = useState(""), [route, setRoute] = useState<ControlEdge["route"]>("next");
  const [rawScope, setRawScope] = useState<string | null>(null);
  const [rawScopeBase, setRawScopeBase] = useState<string | null>(null);
  const edits = useMemo(() => new DraftEdits(commands.session, catalog), [commands, catalog]);
  useEffect(() => { const a = commands.subscribe(refresh), b = catalog.subscribe(refresh), c = commands.rebase.subscribe(refresh); void catalog.refresh(); return () => { a(); b(); c(); }; }, [commands, catalog, refresh]);
  const session = commands.session.snapshot, discovery = catalog.snapshot, command = commands.snapshot, rebase = commands.rebase.snapshot;
  const disabled = session.denied || discovery.phase === "denied";
  useEffect(() => { if (discovery.phase === "denied" && !session.denied) commands.deny(); }, [commands, discovery.phase, session.denied]);
  useEffect(() => { if (session.denied && discovery.phase !== "denied") catalog.deny(); }, [catalog, discovery.phase, session.denied]);
  let scope: ExecutableScopeV4 | undefined;
  try { scope = edits.scope(path); } catch { /* An acknowledged replacement can remove this nested scope. */ }
  const nodes = scope?.nodes ?? [], ids = new Set(nodes.map(node => node.node_id)), ambiguous = ids.size !== nodes.length;
  const offset = nodes.findIndex(node => node.node_id === selected) >= 200 ? 200 : 0;
  const shown = ambiguous ? [] : nodes.slice(offset, offset + 200), visible = new Set(shown.map(node => node.node_id));
  const links = (scope?.edges ?? []).flatMap((edge, index) => visible.has(edge.source) && visible.has(edge.target)
    ? [{ id: String(index), source: edge.source, target: edge.target }] : []);
  const selectedNode = ambiguous ? undefined : nodes.find(node => node.node_id === selected);
  const rawScopeStale = rawScope !== null && rawScopeBase !== JSON.stringify(scope, null, 2);
  const perform = (action: () => void) => { try { action(); setError(null); refresh(); } catch (failure) { setError(failure instanceof Error ? failure.message : "Draft change could not be applied."); } };
  const submit = (action: "save" | "validate" | "reconcile") => {
    try { const pending = action === "reconcile" ? commands.reconcile() : commands[action](crypto.randomUUID()); void pending; setError(null); }
    catch { setError("Command unavailable. Resolve the current command or save the draft first."); }
  };
  return <div className="workspace draft-workspace">
    <header><span className="brand">AMPHORA<span>research studio</span></span><div className="mode">Design</div><span className="fixture">{synthetic ? "Synthetic authoring fixture" : "Next-campaign draft"}</span></header>
    <main>
      <div className="context"><div><p className="eyebrow">Campaign / next revision</p><h1>Compose a campaign</h1></div><p>Saved revision {session.base?.head.revision ?? "none"} · {session.dirty ? "Local changes" : "Saved"}</p></div>
      <div className="toolbar"><label>Draft title<input disabled={disabled} value={session.local.title} maxLength={200} onChange={event => perform(() => commands.session.edit({ ...session.local, title: event.target.value }))} /></label>
        <button disabled={disabled || !!session.pending} onClick={() => submit("save")}>Save draft</button>
        <button disabled={disabled || !!session.pending || session.dirty || !session.base} onClick={() => submit("validate")}>Validate saved revision</button>
        {session.pending && command.phase !== "conflict" && <button disabled={disabled || command.phase !== "unresolved"} onClick={() => submit("reconcile")}>Check original receipt</button>}
        <button disabled={disabled || !!session.pending || rebase.phase === "loading"} onClick={() => void commands.rebase.review()}>Review latest saved revision</button>
        <button disabled={!session.base || disabled} onClick={() => setCompare(value => !value)}>Compare with saved revision</button>
      </div>
      <p role="status">{disabled ? "Access denied. Local draft retained; transmission disabled." : session.pending ? `Command ${command.phase}. Local edits are retained.` : session.reason ? `Command rejected: ${session.reason}` : "Draft changes apply to a future campaign. No active run is changed."}</p>
      {command.phase === "conflict" && <p role="alert">Command identity conflicted. Local edits are retained; the existing receipt belongs to a different request. No replacement command was sent.</p>}
      {error && <p role="alert">{error}</p>}
      {rebase.phase === "loading" && <p role="status">Loading the latest saved revision for review.</p>}
      {rebase.phase === "unavailable" && <p role="status">No newer compatible revision could be loaded ({rebase.reason}). Local work is unchanged.</p>}
      {rebase.phase === "applied" && <p role="status">Base updated. Save remaining local changes and validate again before activation.</p>}
      {rebase.phase === "ready" && rebase.head && !disabled && <section aria-label="Review newer saved revision">
        <h2>Review saved revision {rebase.head.head.revision}</h2>
        <p>The comparison shows how your local content differs from this saved revision. Keeping local content replaces these differences on your next save; nothing is merged automatically.</p>
        <DraftComparisonView comparison={new DraftComparison({ title: rebase.head.head.title, definition: rebase.head.definition }, session.local)} />
        <button disabled={!!session.pending} onClick={() => perform(() => commands.rebase.apply())}>Keep local draft on revision {rebase.head.head.revision}</button>
      </section>}
      {session.validation && <p>Validation of revision {session.validation.revision}: {session.validation.structurally_valid ? "structurally valid" : "findings require repair"} · {session.validationMatchesDraft ? "matches saved draft" : "historical result"}. Scientific applicability is not established.</p>}
      {session.validation?.findings.map((finding, index) => <p key={index}>{finding.code}: {finding.message}</p>)}
      {compare && session.base && !disabled ? <DraftComparisonView comparison={new DraftComparison({ title: session.base.head.title, definition: session.base.definition }, session.local)} /> : <>
        <div className="toolbar"><span>Scope: {path.length ? path.join(" / ") : "Root"}</span><button disabled={!path.length} onClick={() => { setPath(value => value.slice(0, -1)); select(null); setRawScope(null); }}>Parent scope</button>
          <label>New node ID<input disabled={disabled} value={nodeId} maxLength={128} onChange={event => setNodeId(event.target.value)} /></label>
          <label>Reviewed tool<select aria-label="Reviewed tool" disabled={disabled || discovery.phase !== "ready"} value={descriptor} onChange={event => setDescriptor(event.target.value)}><option value="">Choose a tool</option>
            {discovery.choices?.map(choice => <option key={choice.release.lock.descriptor_sha256} disabled={!choice.authoringAvailable} value={choice.release.lock.descriptor_sha256}>{choice.release.descriptor.tool.purpose} · {choice.release.lock.tool.release}{choice.authoringAvailable ? "" : ` (${choice.reasons.join(", ")})`}</option>)}
          </select></label>
          <button disabled={disabled || !descriptor || discovery.phase !== "ready"} onClick={() => perform(() => { edits.insertTool(path, nodeId, descriptor); select(nodeId); })}>Add tool</button>
          <button disabled={disabled} onClick={() => perform(() => edits.insert(path, { kind: "finish", node_id: nodeId, outputs: [] }))}>Add finish</button>
          <button disabled={disabled || discovery.phase === "loading"} onClick={() => void catalog.refresh()}>Refresh tool library</button>
          {discovery.nextAfter && <button disabled={disabled || discovery.phase !== "ready"} onClick={() => void catalog.refresh(discovery.nextAfter)}>Next tool page</button>}
        </div>
        <p className="status">{discovery.phase === "loading" ? "Loading tool library…" : discovery.phase === "stale" ? "Tool library is stale. Refresh before selecting a release." : `${discovery.choices?.length ?? 0} tools on this page.`} {shown.length}/{nodes.length} nodes shown; {(scope?.edges?.length ?? 0) - links.length} links outside the canvas or unresolved. Draft links are unvalidated.</p>
        {!scope && <p role="alert">This scope is no longer present. Return to its parent.</p>}
        {ambiguous && <p role="alert">Duplicate node identities. Repair the scope source before using node forms.</p>}
        <div className="work-area draft-area"><GraphCanvas key={JSON.stringify(path)} label="Draft graph workspace" nodes={shown.map((node, index) => ({ id: node.node_id, label: node.node_id, status: `${node.kind} · draft`, x: index % 4 * 245, y: Math.floor(index / 4) * 100 }))} edges={links} selection={selected} select={select} />
          <aside className="draft-sidebar"><nav aria-label="Draft nodes">{nodes.map((node, index) => <button key={index} disabled={ambiguous} aria-pressed={selected === node.node_id} onClick={() => select(node.node_id)}>{node.node_id} · {node.kind}</button>)}</nav>
            {selectedNode && <DraftInspector key={JSON.stringify([path, selectedNode.node_id])} node={selectedNode} edits={edits} path={path} catalog={catalog} disabled={disabled} perform={perform} selectNode={select}
              openScope={() => { setPath([...path, selectedNode.node_id]); select(null); setRawScope(null); }} />}
          </aside></div>
        <details><summary>Control links</summary><div className="toolbar">
          <label>From node<select aria-label="From node" value={edgeSource} onChange={event => setEdgeSource(event.target.value)}><option value="">Choose source</option>{nodes.map((node, index) => <option key={index}>{node.node_id}</option>)}</select></label>
          <label>To node<select aria-label="To node" value={edgeTarget} onChange={event => setEdgeTarget(event.target.value)}><option value="">Choose target</option>{nodes.map((node, index) => <option key={index}>{node.node_id}</option>)}</select></label>
          <label>Route<select aria-label="Route" value={route} onChange={event => setRoute(event.target.value as ControlEdge["route"])}><option>next</option><option>true</option><option>false</option></select></label>
          <button disabled={disabled || !edgeSource || !edgeTarget} onClick={() => perform(() => edits.connect(path, { source: edgeSource, target: edgeTarget, ...(route ? { route } : {}) }))}>Add control link</button>
        </div><ul>{scope?.edges?.map((edge, index) => <li key={index}>{edge.source} → {edge.target} ({edge.route ?? "next"}) <button disabled={disabled} onClick={() => perform(() => edits.disconnect(path, index))}>Remove link {index + 1}</button></li>)}</ul></details>
        {scope && <details><summary>Advanced scope definition</summary><label>Scope JSON<textarea aria-label="Scope JSON" disabled={disabled} rows={16} value={rawScope ?? JSON.stringify(scope, null, 2)} maxLength={262144} onChange={event => { if (rawScope === null) setRawScopeBase(JSON.stringify(scope, null, 2)); setRawScope(event.target.value); }} /></label>
          {rawScopeStale && <p>The scope changed after this source edit began. Copy your changes before reloading its current definition.</p>}
          <button disabled={disabled || rawScope === null || rawScopeStale} onClick={() => perform(() => { const next = parseDraftJSON(rawScope!) as ExecutableScopeV4;
            if (path.length) { const parent = edits.scope(path.slice(0, -1)), node = parent.nodes.find(item => item.node_id === path.at(-1))!;
              if (node.kind !== "iterate" && node.kind !== "scatter") throw new Error("Scope unavailable."); edits.replace(path.slice(0, -1), node.node_id, { ...node, body: next });
            } else commands.session.edit({ ...session.local, definition: { ...session.local.definition, body: next } }); setRawScope(null); })}>Apply scope definition</button>
          <button disabled={disabled} onClick={() => { setRawScope(null); setRawScopeBase(null); }}>Reload scope source</button>
        </details>}
      </>}
      <footer>Save retains a draft revision. Validation is structural; activation and current tool eligibility are separate owner checks.</footer>
    </main>
  </div>;
}
