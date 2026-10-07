/** Reproducible consumer types and schema bytes; Python publications remain authoritative. */
import { createHash } from "node:crypto";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { resolve, dirname } from "node:path";
import { compile } from "json-schema-to-typescript";
import { standaloneValidators } from './standalone-validators.mjs';

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = resolve(root, "../contracts/schemas/v1");
const target = resolve(root, "src/contracts/generated");
const roots = {
  snapshot: ["graph-runtime.snapshot-page", "GraphSnapshotPage"],
  detail: ["graph-runtime.node-detail", "GraphNodeDetail"],
  values: ["graph-runtime.value-page", "GraphValuePage"],
  events: ["graph-runtime.invalidation-page", "GraphInvalidationPage"],
  scopes: ["graph-runtime.scope-page", "GraphScopePage"],
  topology: ["graph-runtime.topology-page", "GraphTopologyPage"],
  catalog: ["graph-runtime.view-catalog", "GraphViewCatalog"],
  lineage: ["graph-runtime.successor-lineage", "SuccessorLineage"],
  completion: ["runtime.completion-record", "CompletionRecord"],
  artifact: ["core.artifact-ref", "ArtifactRef"],
};
const authoringRoots = {
  save: ["graph-runtime.draft-save", "SaveDraft"],
  validate: ["graph-runtime.draft-validate", "ValidateDraft"],
  draft: ["graph-runtime.draft-revision", "DraftRevision"],
  page: ["graph-runtime.draft-page", "DraftPage"],
  validation: ["graph-runtime.draft-validation", "DraftValidation"],
  receipt: ["graph-runtime.draft-command-receipt", "DraftCommandReceipt"],
  admit: ["graph-runtime.draft-admission", "AdmitDraft"],
  universe: ["graph-runtime.definition-universe", "DefinitionUniverse"],
  schema: ["graph-runtime.definition-schema", "DefinitionSchema"],
  releases: ["tools.release-page", "ReleasePage"],
  release: ["tools.release-snapshot", "ReleaseSnapshot"],
  cancel: ["runtime.cancel", "CancelRun"],
  execution_receipt: ["runtime.receipt", "CommandReceipt"],
  identity: ["commands.identity", "CommandIdentity"],
};
const knowledgeRoots = {
  search_request: ["knowledge.entity-search-request", "GraphEntitySearchRequest"],
  search_page: ["knowledge.entity-search-page", "GraphEntitySearchPage"],
  neighborhood_request: ["knowledge.neighborhood-request", "GraphNeighborhoodRequest"],
  neighborhood_page: ["knowledge.neighborhood-page", "GraphNeighborhoodPage"],
  object_request: ["knowledge.object-request", "GraphObjectRequest"],
  object_detail: ["knowledge.object-detail", "GraphObjectDetail"],
  catalog: ["knowledge.explore-catalog", "GraphExploreCatalog"],
};
const researchRoots = {
  specimen_request: ["research-views.specimen-view-request", "SpecimenViewRequest"],
  specimen_page: ["research-views.specimen-view-page", "SpecimenViewPage"],
  property_request: ["research-views.property-view-request", "PropertyViewRequest"],
  property_page: ["research-views.property-view-page", "PropertyViewPage"],
  series_request: ["research-views.observation-series-request", "ObservationSeriesRequest"],
  series_page: ["research-views.observation-series-page", "ObservationSeriesPage"],
  catalog: ["research-views.catalog", "ResearchViewCatalog"],
};
const provenanceRoots = {
  "artifact": [
    "core.artifact-ref",
    "ArtifactRef"
  ],
  "source": [
    "evidence.source-revision",
    "SourceRevision"
  ],
  "span": [
    "evidence.source-span",
    "SourceSpan"
  ],
  "trace": [
    "evidence.conversion-trace",
    "ConversionTrace"
  ],
  "trace_ref": [
    "evidence.conversion-trace-ref",
    "ConversionTraceRef"
  ],
  "derivation": [
    "artifacts.derivation-receipt",
    "DerivationReceipt"
  ],
  "material": [
    "research.material-state-revision",
    "MaterialStateRevision"
  ],
  "experiment": [
    "research.experiment-definition",
    "ExperimentDefinition"
  ],
  "observation": [
    "research.observation-revision",
    "ObservationRevision"
  ],
  "question": [
    "research.question",
    "ResearchQuestion"
  ],
  "need": [
    "research.evidence-need",
    "EvidenceNeed"
  ],
  "interpretation_selection": [
    "research.interpretation-selection",
    "InterpretationSelection"
  ],
  "interpretation_ref": [
    "research.interpretation-ref",
    "InterpretationRef"
  ],
  "interpretation": [
    "research.interpretation-status",
    "InterpretationStatus"
  ],
  "observation_correction": [
    "research.observation-correction-view",
    "ObservationCorrectionView"
  ],
  "material_correction": [
    "research.material-state-correction-view",
    "MaterialStateCorrectionView"
  ]
};
const feedbackRoots = {
  "assessment_request": [
    "research.assessment-request",
    "EvidenceAssessmentRequest"
  ],
  "assessment": [
    "research.assessment-status",
    "EvidenceAssessmentStatus"
  ],
  "publication_request": [
    "research.assessment-publication-request",
    "AssessmentPublicationRequest"
  ],
  "publication": [
    "research.assessment-publication-status",
    "AssessmentPublicationStatus"
  ],
  "assessment_selection": [
    "research.select-assessment-receipt",
    "SelectAssessmentReceipt"
  ],
  "reasoning_selection": [
    "knowledge.select-reasoning-receipt",
    "SelectReasoningReceipt"
  ],
  "correction": [
    "graph-runtime.receipt-correction-view",
    "ReceiptCorrectionView"
  ],
  "proposal": [
    "knowledge.proposal-status",
    "GraphProposalStatus"
  ],
  "change": [
    "knowledge.accepted-change",
    "AcceptedGraphChange"
  ]
};
const check = process.argv.includes("--check");
async function generate(roots, target) {
  const manifest = {};
  const schemas = {};
  await mkdir(target, { recursive: true });

  async function output(name, body) {
    const path = resolve(target, name);
    if (check) {
      const old = await readFile(path, "utf8").catch(() => "");
      if (old !== body) throw new Error(`Generated contract drift: ${name}; run npm run generate`);
    } else {
      await writeFile(path, body, "utf8");
    }
  }

  for (const [key, [file, title]] of Object.entries(roots)) {
    const bytes = await readFile(resolve(source, `${file}.serialization.json`));
    const schema = JSON.parse(bytes);
    schemas[key] = schema;
    manifest[key] = { source: `contracts/schemas/v1/${file}.serialization.json`, sha256: createHash("sha256").update(bytes).digest("hex") };
    const declarations = await compile(schema, title, {
      bannerComment: "/* Generated from the published Python-owned serialization schema. Do not edit. */",
      additionalProperties: false, ignoreMinAndMaxItems: true, unknownAny: true,
    });
    await output(`${key}.d.ts`, declarations);
  }
  await output("schemas.json", JSON.stringify(schemas, null, 2) + "\n");
  await output("manifest.json", JSON.stringify(manifest, null, 2) + "\n");
  await output("validators.ts", await standaloneValidators(schemas, root));
  console.log(`Studio contracts ${check ? "verified" : "generated"}: ${Object.keys(roots).length} published roots`);
}

await generate(roots, target);
await generate(authoringRoots, resolve(target, "authoring"));

await generate(knowledgeRoots, resolve(target, "knowledge"));
await generate(researchRoots, resolve(target, "research"));

await generate(provenanceRoots, resolve(target, "provenance"));

await generate(feedbackRoots, resolve(target, "feedback"));

await generate({
  checkpoints: ["supervision.checkpoint-inspection-page", "CheckpointInspectionPage"],
  requests: ["supervision.checkpoint-request-page", "CheckpointRequestPage"],
  context: ["supervision.checkpoint-context-page", "CheckpointContextPage"],
  responses: ["supervision.checkpoint-response-page", "CheckpointResponsePage"],
  decision: ["supervision.checkpoint-decision", "CheckpointDecision"],
}, resolve(target, "supervision"));
