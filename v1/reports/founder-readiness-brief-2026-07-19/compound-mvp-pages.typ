#let compound-mvp-pages(
  page-title,
  panel-box,
  source-note,
  bullet-line,
  subsection,
  navy,
  blue,
  green,
  amber,
  red,
  red-light,
) = [
// PAGE 9 — MVP20 FEEDBACK/V5 INPUT TRUTH
#page-title(
  "09 / MVP20 FEEDBACK V5 — INPUT TRUTH",
  [A strong use-case charter. Not yet a scientific dataset.],
  [The adjacent mvp20/feedback/v5 material sharply defines the desired marine-primer outcome and autonomous-engine behavior. It does not contain a catalog, measured candidate rows, a known-solution benchmark, or evidence that a formulation meets the envelope.],
)

#table(
  columns: (2.1fr, 0.48fr, 2.35fr, 1.25fr),
  table.header(
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[EXACT SOURCE PATH]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[BYTES]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[SHA-256]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[CLASSIFIED ROLE]],
  ),
  text(size: 6.3pt)[/home/ubuntu/amphora/build/mvp20/feedback/v5/txt.txt],
  text(size: 6.3pt)[657],
  text(size: 6.3pt)[57abc1e3dca20849877401d23d46d3af09642a339a63b238549aed0a28f1a2a9],
  text(size: 6.3pt)[Problem framing],
  text(size: 6.3pt)[/home/ubuntu/amphora/build/mvp20/feedback/v5/txt1.txt],
  text(size: 6.3pt)[3,813],
  text(size: 6.3pt)[1dfdc6f8005bc493d6f0d5433dff1aa2e92c7b1e49594c2acc7671aa8fa699d9],
  text(size: 6.3pt)[Technical envelope],
  text(size: 6.3pt)[/home/ubuntu/amphora/build/mvp20/feedback/v5/txt2.txt],
  text(size: 6.3pt)[8,049],
  text(size: 6.3pt)[43494f433ca79733cc73d3afcb9c2ab101f506dd51f26f8164eaa10995f842ac],
  text(size: 6.3pt)[Engine charter],
)

#v(5pt)
#block(width: 100%, fill: rgb("#E6F0F6"), stroke: 0.6pt + blue, radius: 4pt, inset: 6pt, [#text(size: 6.3pt, weight: "bold", fill: blue)[CLASSIFICATION] #h(6pt) #text(size: 6.3pt)[REQUIREMENTS_AND_ENGINE_CHARTER_ONLY · authoritative as founder requirements · not measured scientific evidence]])

#v(8pt)
#grid(
  columns: (1fr, 1fr),
  column-gutter: 8pt,
  panel-box([WHAT THE FILES GIVE THE ENGINE], [
    #bullet-line([A precise first use case.], [Marine steel, immersion-service intent, two-component epoxy-polyamide, solvent-borne application.], tone: "green")
    #bullet-line([A constraint surface.], [1:1 volume mix; approximately 65% volume solids; VOC, film, cure, storage, and application targets.], tone: "green")
    #bullet-line([An operating doctrine.], [Self-directed model selection; auditable reasoning; explicit assumptions; empirical feedback.], tone: "green")
    #bullet-line([A product narrative.], [A clean founder-level definition of why the engine matters and how the loop should work.], tone: "green")
  ], tone: "green", height: 1.82in),
  panel-box([WHAT THE FILES DO NOT GIVE THE ENGINE], [
    #bullet-line([No machine-readable v5 snapshot.], [There is no feedback/v5/catalog.json or immutable acquisition/normalization receipt.], tone: "red")
    #bullet-line([No truth set.], [No labeled known formulations, measured endpoints, custody, rights, uncertainty, or method metadata.], tone: "red")
    #bullet-line([No candidate result.], [No unknown structure, formulation, campaign replay, CRO result, or independent review.], tone: "red")
    #bullet-line([No authority.], [The charter cannot establish safety, compliance, qualification, performance, novelty, FTO, procurement, or execution readiness.], tone: "red")
  ], tone: "red", height: 1.82in),
)

#v(8pt)
#block(width: 100%, fill: navy, radius: 5pt, inset: 9pt, [
  #text(size: 6.3pt, weight: "bold", fill: rgb("#8EC6E6"), tracking: 0.08em)[FOUNDER INTERPRETATION]
  #v(3pt)
  #text(size: 11.5pt, weight: "bold", fill: white)[The MVP win is not “produce a recipe from three prompts.” It is “turn this envelope into a governed experiment that recognizes known controls, proposes unknowns, and learns from measured outcomes without laundering a score into a product claim.”]
])

#v(6pt)
#source-note([Direct source inspected: /home/ubuntu/amphora/build/mvp20/feedback/v5. All three source hashes are recorded in the report evidence snapshot.])

#pagebreak()

// PAGE 10 — KNOWN GENERATION ZERO
#page-title(
  "10 / KNOWN GENERATION-0 CONTROLS",
  [Known chemistry must be visible, useful, and never mistaken for novelty.],
  [A mixed cohort is the fastest credible demonstration: familiar controls prove identity, group counting, role logic, arithmetic, and abstention before unmade proposals are allowed to look impressive.],
)

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  column-gutter: 6pt,
  panel-box([EA-P10 / DGEBA-LIKE MODEL], [#text(size: 6.3pt)[Known-family epoxide anchor. Expected origin: KNOWN_GENERATION_0. Novelty posture: KNOWN_CONTROL_NOT_NOVEL.]], tone: "blue", height: 0.84in),
  panel-box([EA-P09 / BISPHENOL-F MODEL], [#text(size: 6.3pt)[Known-family epoxide comparator with a distinct aromatic scaffold context. Not a product recommendation.]], tone: "blue", height: 0.84in),
  panel-box([EA-P12 / DIETHYLENETRIAMINE], [#text(size: 6.3pt)[Known polyamine positive-role control for reactive amine-H accounting and equivalent arithmetic.]], tone: "blue", height: 0.84in),
  panel-box([EA-P19 / IPDA MODEL], [#text(size: 6.3pt)[Known-family cycloaliphatic diamine model for scaffold and role diversity checks.]], tone: "blue", height: 0.84in),
)

#v(8pt)
#grid(
  columns: (1.12fr, 1fr),
  column-gutter: 8pt,
  panel-box([HOW A KNOWN CONTROL CAN BE “INTERESTING”], [
    #bullet-line([Attention, not rank.], [INTERESTING_FOR_AUDIT means the record exercises a useful mechanism, scaffold, role, or failure boundary.], tone: "amber")
    #bullet-line([Expected positive.], [The control should pass identity and applicable chemistry checks when the toolchain and ontology are valid.], tone: "amber")
    #bullet-line([Expected comparison.], [Its outcomes establish whether unknowns receive the same treatment and whether the system can recover obvious chemistry.], tone: "amber")
    #bullet-line([Explicit ceiling.], [The flag does not mean novel, superior, compliant, safe, purchasable, qualified, or predicted to meet the coating envelope.], tone: "red")
  ], tone: "amber", height: 1.87in),
  panel-box([MINIMUM KNOWN-CONTROL RECEIPT], [
    #bullet-line([Origin.], [KNOWN_GENERATION_0 plus source artifact and structure hash.], tone: "blue")
    #bullet-line([Identity.], [Canonical isomeric SMILES, InChIKey, formula, mass, scaffold, packed fingerprint.], tone: "blue")
    #bullet-line([Chemistry.], [Reactive atom indices, oxirane or amine-H count, rejection code, toolkit manifest hash.], tone: "blue")
    #bullet-line([Traversal.], [One typed outcome for all 29 modules; missing science is ABSTAIN or NOT_APPLICABLE.], tone: "blue")
    #bullet-line([Claim locks.], [RANK: NONE and FINAL AGGREGATE SCORE: NOT AUTHORIZED.], tone: "red")
  ], tone: "blue", height: 1.87in),
)

#v(8pt)
#subsection([THE MVP TEST / KNOWN RECOVERY])
#v(4pt)
#table(
  columns: (1.05fr, 1.42fr, 1.5fr, 1.45fr),
  table.header(
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[TEST]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[EXPECTED BEHAVIOR]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[PASS EVIDENCE]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[FAIL / STOP]],
  ),
  [Known identity], [Recover canonical identity reproducibly], [Portable/optimized parity; byte-identical replay], [Identity, stereo, formula, mass, or fingerprint drift],
  [Known role], [Recognize applicable epoxide or reactive amine control], [Signed ontology atom-index evidence], [Heuristic-only flag or missing atom indices],
  [Known pairing context], [Compute typed equivalent balance without candidate overrides], [Finite unit-bound EEW/AHEW calculation], [Zero groups, inversion, non-finite input, or override],
  [Known attention flag], [Surface as useful control without a rank], [Reason code + origin + claim locks], [Any novelty, superiority, compliance, or product-performance claim],
)

#v(5pt)
#source-note([The EA-P identifiers are pre-campaign audit probes from reports/data/epoxy-amine-20-audit-probes.v1.json. They are not campaign participants, formulations, or validated solutions.])

#pagebreak()

// PAGE 11 — UNKNOWN PROPOSALS
#page-title(
  "11 / UNKNOWN, UNMADE PROPOSALS",
  [Unknowns run beside controls—not on a privileged path.],
  [The locked ORD grammar is intended to generate unmade structures with reaction lineage. Unknown origin is preserved; potential novelty remains a question until exact structure, literature, patent, rights, and independent-review work is complete.],
)

#grid(
  columns: (1fr, auto, 1fr, auto, 1fr, auto, 1fr),
  column-gutter: 5pt,
  panel-box([1 / HOST REQUEST], text(size: 6.3pt)[Family + host-selected parents; no product structure], tone: "blue", height: 0.75in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([2 / AUTHORIZED GRAMMAR], text(size: 6.3pt)[Extraction-only ORD lineage and signed hashes], tone: "blue", height: 0.75in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([3 / NATIVE CHEMISTRY], text(size: 6.3pt)[Typed RDKit facts, rejects, duplicates, atom evidence], tone: "blue", height: 0.75in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([4 / MIXED COHORT], text(size: 6.3pt)[Known controls + unknowns; one traversal policy], tone: "green", height: 0.75in),
)

#v(8pt)
#grid(
  columns: (1fr, 1fr),
  column-gutter: 8pt,
  panel-box([WHAT MAKES AN UNKNOWN WORTH INSPECTING], [
    #bullet-line([Valid chemistry record.], [Single-component, supported valence/elements, stable canonical identity, complete lineage.], tone: "green")
    #bullet-line([Role evidence.], [Signed ontology finds relevant atoms; molecule facts support a resin or hardener audit context.], tone: "green")
    #bullet-line([Coverage value.], [Adds scaffold or mechanism coverage to the bounded 20-card/12-pair audit cohort.], tone: "green")
    #bullet-line([Transparent uncertainty.], [Every missing endpoint, source, safety, process, or performance fact remains explicit.], tone: "green")
  ], tone: "green", height: 1.75in),
  panel-box([WHAT “POTENTIALLY NOVEL” MUST MEAN], [
    #bullet-line([Permitted wording.], [Potential novelty is NOT_ESTABLISHED; review follow-up only.], tone: "amber")
    #bullet-line([Required checks.], [Structure deduplication, source lineage, literature and patent searches, date-bounded evidence, and counsel-defined FTO scope.], tone: "amber")
    #bullet-line([Separation.], [Novelty observations cannot become an aggregate score or override chemistry, rights, safety, or evidence gates.], tone: "red")
    #bullet-line([Current truth.], [No locked-grammar unknown has been generated here because ORD objects, toolchains, rights receipts, and signatures remain incomplete.], tone: "red")
  ], tone: "amber", height: 1.75in),
)

#v(8pt)
#subsection([TWO CONCEPTUAL NOVELTY-REVIEW EXAMPLES / REQUEST LINEAGE ONLY])
#v(4pt)
#table(
  columns: (0.72fr, 1.35fr, 2.45fr, 0.75fr, 1.35fr),
  table.header(
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[REQUEST]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[AUTHORIZED FAMILY]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[EXACT HOST PARENTS]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[ROLE]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[CURRENT POSTURE]],
  ),
  text(size: 6.3pt)[resin-12],
  text(size: 6.3pt)[ORD_GLYCIDYL_ETHER_FORMATION],
  text(size: 6.3pt)[Oc1ccc(S(=O)(=O)c2ccc(O)cc2)cc1 + ClCC1CO1],
  text(size: 6.3pt)[resin],
  text(size: 6.3pt, weight: "bold", fill: red)[UNMADE · NOT_ESTABLISHED · AUDIT_ONLY],
  text(size: 6.3pt)[hardener-07],
  text(size: 6.3pt)[ORD_REDUCTIVE_AMINATION],
  text(size: 6.3pt)[NCc1ccccc1CN + CC=O],
  text(size: 6.3pt)[hardener],
  text(size: 6.3pt, weight: "bold", fill: red)[UNMADE · NOT_ESTABLISHED · AUDIT_ONLY],
)

#v(7pt)
#block(width: 100%, fill: red-light, stroke: 0.6pt + red, radius: 4pt, inset: 7pt, [#text(size: 6.5pt, weight: "bold", fill: red)[CURRENT GATE] #text(size: 6.3pt)[ Deterministic seed 20260719 and the request records are charter inputs. No product structure, ORD reaction/dataset lineage, campaign card, or measured result exists. The examples do not invent campaign structures and authorize no safety, synthesis, execution, novelty, or performance claim.]])

#pagebreak()

// PAGE 12 — CENTRAL SOLVER
#page-title(
  "12 / CENTRAL SOLVER + ADAPTIVE LOOP",
  [Many models emit typed evidence. One central policy solver decides what may influence selection.],
  [The solver does not average 29 scores. It composes PASS, FAIL, ABSTAIN, and NOT_APPLICABLE outcomes under authority, applicability, evidence-strength, and coverage rules. Adaptation begins only from a signed, candidate-bound empirical return.],
)

#grid(
  columns: (1fr, auto, 1.15fr, auto, 1fr),
  column-gutter: 5pt,
  panel-box([MIXED GENERATION 0], [#text(size: 6.3pt)[Known controls + locked unknowns + explicit rejects and duplicates]], tone: "blue", height: 0.78in),
  align(center + horizon)[#text(size: 14pt, weight: "bold", fill: blue)[→]],
  panel-box([29 MODULE OUTCOMES], [#text(size: 6.3pt)[PASS / FAIL / ABSTAIN / NOT_APPLICABLE; scalar only when typed and unit-bound]], tone: "blue", height: 0.78in),
  align(center + horizon)[#text(size: 14pt, weight: "bold", fill: blue)[→]],
  panel-box([CENTRAL POLICY SOLVER], [#text(size: 6.3pt)[Authority, applicability, evidence strength, coverage, claim locks, and objective checks]], tone: "amber", height: 0.78in),
)

#v(5pt)
#align(center)[#text(size: 15pt, weight: "bold", fill: blue)[↓]]
#v(2pt)
#grid(
  columns: (1fr, auto, 1fr, auto, 1fr),
  column-gutter: 5pt,
  panel-box([12 AUDIT PAIRS], [#text(size: 6.3pt)[Deterministic coverage; typed equivalent balances; no formulation-performance claim]], tone: "blue", height: 0.76in),
  align(center + horizon)[#text(size: 14pt, weight: "bold", fill: blue)[→]],
  panel-box([CRO FEASIBILITY DRAFTS], [#text(size: 6.3pt)[Controls, custody, immutable holds; execution_authorized: false]], tone: "blue", height: 0.76in),
  align(center + horizon)[#text(size: 14pt, weight: "bold", fill: blue)[→]],
  panel-box([SIGNED MEASURED RETURN], [#text(size: 6.3pt)[Candidate-bound observations, method, uncertainty, deviations, rights, and distinct signatures]], tone: "green", height: 0.76in),
)

#v(8pt)
#grid(
  columns: (1fr, 1fr),
  column-gutter: 8pt,
  panel-box([WHAT ADAPTS], [
    #bullet-line([Calibration.], [Within a locked endpoint and applicability domain, predictions can be recalibrated from measured residuals.], tone: "green")
    #bullet-line([Uncertainty.], [Abstention regions and confidence bounds can tighten or widen from observed coverage.], tone: "green")
    #bullet-line([Experimental allocation.], [After authority exists, the next round can emphasize information gain while retaining controls.], tone: "green")
    #bullet-line([Method status.], [A model can be held, revised, or promoted only through preregistered evaluation and independent review.], tone: "green")
  ], tone: "green", height: 1.78in),
  panel-box([WHAT DOES NOT ADAPT SILENTLY], [
    #bullet-line([Claim locks.], [No feedback can enable rank, procurement, synthesis, safety, qualification, or performance authority.], tone: "red")
    #bullet-line([Truth labels.], [Known controls never become “novel”; failed experiments never disappear.], tone: "red")
    #bullet-line([Splits.], [Extraction, validation, and held-out partitions remain hash-locked; held-out data never enters training or PGO.], tone: "red")
    #bullet-line([Methods.], [No automatic model swap, threshold weakening, candidate override, or unreviewed objective change.], tone: "red")
  ], tone: "red", height: 1.78in),
)

#v(7pt)
#block(width: 100%, fill: navy, radius: 5pt, inset: 8pt, [
  #text(size: 6.3pt, weight: "bold", fill: rgb("#8EC6E6"), tracking: 0.08em)[INITIAL MVP WIN]
  #v(3pt)
  #text(size: 10.5pt, weight: "bold", fill: white)[Recover known controls, generate valid unknowns, explain why each is surfaced, package a replayable audit cohort, and ingest one independently measured return—without producing an unauthorized rank.]
])

#pagebreak()

// PAGE 13 — STRENGTHS, WEAKNESSES, CLOSURE
#page-title(
  "13 / WHAT IS STRONG, WHAT IS WEAK, HOW IT CLOSES",
  [The control architecture is credible. The compound science is not yet demonstrated.],
  [This distinction is the core founder message: engineering trust is an asset, but it becomes a product only when real chemistry, rights, replay, and measured feedback close the loop.],
)

#grid(
  columns: (1fr, 1fr),
  column-gutter: 8pt,
  panel-box([STRONG NOW], [
    #bullet-line([Fail-closed authority.], [Eight signed Phase-0 controls keep ranking and product claims disabled.], tone: "green")
    #bullet-line([Deterministic contracts.], [JCS v2 hashing, exact artifact bindings, typed module outcomes, and separate scientific/execution receipts are implemented foundations.], tone: "green")
    #bullet-line([Native ORD foundation.], [Pinned acquisition verifies 550 object hashes/sizes, gzip integrity, and explicit Parquet exclusion; vendored protobuf codegen removes host protoc assumptions.], tone: "green")
    #bullet-line([Toolchain contract.], [Portable and optimized RDKit profiles are separately hash-bound with ABI, CPU, SBOM, and parity requirements.], tone: "green")
    #bullet-line([Honest reporting.], [The final verified report path is protected from fixture chemistry and premature success claims.], tone: "green")
  ], tone: "green", height: 2.05in),
  panel-box([WEAK / BLOCKED NOW], [
    #bullet-line([Input evidence.], [mvp20/feedback/v5 is three narrative files, not a machine-readable benchmark or measured corpus.], tone: "red")
    #bullet-line([Chemistry runtime.], [No verified portable/optimized RDKit installation exists in artifacts/toolchains.], tone: "red")
    #bullet-line([Campaign evidence.], [No acquired ORD objects, split, real grammar, generated unknowns, 12 pairs, 20 cards, or campaign replay exists.], tone: "red")
    #bullet-line([External trust.], [Rights receipts, evaluator signature, sealed attack suite, independent review, and replay receipt are absent.], tone: "red")
    #bullet-line([Product loop.], [No candidate-bound wet-lab measurement proves adaptation or any marine-coating endpoint.], tone: "red")
  ], tone: "red", height: 2.05in),
)

#v(8pt)
#subsection([CLOSURE PLAN / EVIDENCE, NOT RHETORIC])
#v(4pt)
#table(
  columns: (0.74fr, 1.38fr, 1.55fr, 1.45fr, 1.15fr),
  table.header(
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[ORDER / OWNER]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[CLOSE]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[PASS RECEIPT]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[FOUNDER VALUE]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[STOP CONDITION]],
  ),
  [1 / Platform], [Build and verify both native RDKit profiles], [Tests, ABI closure, SBOM, provenance, reproducible portable trees], [Trusted chemistry identity and performance baseline], [Any source, ABI, test, CPU, Python, or parity mismatch],
  [2 / Data + chemistry], [Acquire/decode/split ORD and extract two-family grammar], [550 objects; complete reaction/exclusion accounting; zero leakage; real lineage], [Unknown generation grounded in public reaction evidence], [Missing object, corrupt protobuf, leakage, or unsupported family],
  [3 / Data + science], [Materialize real feedback/v5 benchmark], [300-structure truth cohort, raw PubChem responses, signed ChEBI/PubChem rights], [Known-control recovery has a measurable acceptance test], [Rights, identity, count, or locked threshold failure],
  [4 / Science + assurance], [Run mixed known/unknown campaign + red team], [At least 24 valid structures; 12 pairs; 20 cards; sealed attacks; replay], [Founder-demonstrable compound MVP], [Silent acceptance, rank injection, scientific drift, swap, or memory failure],
  [5 / Lab + evaluator], [Return one independent measured loop], [Signed candidate-bound measurement, method/custody/uncertainty, clean import and recalibration], [First proof that the engine can learn from reality], [Custody, method, rights, or independent-review failure],
)

#v(7pt)
#source-note([No threshold is weakened and no fixture is substituted if a closure step fails. The failure remains a negative result.])
]
