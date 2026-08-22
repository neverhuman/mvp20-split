#let evidence = json("evidence-map.json")

#let navy = rgb("#10243E")
#let navy2 = rgb("#193653")
#let blue = rgb("#2F6F9F")
#let blue-light = rgb("#E6F0F6")
#let paper = rgb("#F6F1E8")
#let panel = rgb("#FFFDF8")
#let ink = rgb("#192A3A")
#let muted = rgb("#607080")
#let rule = rgb("#D7D2C8")
#let green = rgb("#167457")
#let green-light = rgb("#E2F0EA")
#let amber = rgb("#A66100")
#let amber-light = rgb("#F6E8CA")
#let red = rgb("#B4443E")
#let red-light = rgb("#F5E1DE")

#set document(
  title: "Amphora Founder Module + Data Map — 19 July 2026",
  author: "Amphora",
  date: datetime(year: 2026, month: 7, day: 19),
  keywords: ("Amphora", "module map", "datasets", "model methods", "founder brief"),
)

#set page(
  paper: "us-letter",
  flipped: true,
  fill: paper,
  margin: (top: 0.55in, bottom: 0.34in, left: 0.43in, right: 0.43in),
  header: context {
    grid(
      columns: (1fr, auto, auto),
      column-gutter: 14pt,
      text(size: 6.8pt, weight: "semibold", fill: navy)[AMPHORA / MODULE + DATA MAP],
      text(size: 6.5pt, fill: muted)[Founder brief · 19 July 2026],
      text(size: 6.8pt, weight: "semibold", fill: navy)[PAGE #counter(page).display("1") / 5],
    )
    v(3pt)
    line(length: 100%, stroke: 0.7pt + rule)
  },
  footer: context {
    line(length: 100%, stroke: 0.5pt + rule)
    v(2pt)
    grid(
      columns: (1fr, auto),
      text(size: 6.3pt, fill: muted)[Repository-grounded evidence map · “support” does not mean scientific validation or product authority],
      text(size: 6.3pt, fill: muted)[Snapshot: amphora.founder-module-data-map.v1],
    )
  },
)

#set text(font: "Lato", size: 7.8pt, fill: ink, lang: "en")
#set par(leading: 0.54em, justify: false)
#set table(stroke: 0.45pt + rule, inset: (x: 4pt, y: 3.2pt))

#let tone-fill(tone) = if tone == "green" { green-light } else if tone == "amber" { amber-light } else if tone == "red" { red-light } else { blue-light }
#let tone-ink(tone) = if tone == "green" { green } else if tone == "amber" { amber } else if tone == "red" { red } else { blue }
#let ceiling-tone(ceiling) = if ceiling == "CONSTRAINT_ONLY" { "amber" } else if ceiling == "AUDIT_ONLY" { "blue" } else { "red" }

#let kicker(body) = text(size: 6.3pt, weight: "bold", fill: blue, tracking: 0.08em, body)
#let section-title(body) = text(size: 15pt, weight: "bold", fill: navy, body)
#let subsection(body) = text(size: 8.4pt, weight: "bold", fill: navy, body)
#let source-note(body) = text(size: 6.3pt, fill: muted, body)

#let page-title(k, title, dek) = {
  kicker(k)
  v(2pt)
  section-title(title)
  v(2pt)
  text(size: 7.6pt, fill: muted, dek)
  v(7pt)
}

#let tag(body, tone: "blue") = box(
  fill: tone-fill(tone),
  radius: 7pt,
  inset: (x: 5pt, y: 2pt),
  text(size: 6.3pt, weight: "bold", fill: tone-ink(tone), body),
)

#let panel-box(title, body, tone: "blue", height: auto) = block(
  width: 100%,
  height: height,
  fill: panel,
  stroke: (left: 2.5pt + tone-ink(tone), rest: 0.55pt + rule),
  radius: 4pt,
  inset: 8pt,
  [
    #text(size: 7.4pt, weight: "bold", fill: tone-ink(tone))[#title]
    #v(4pt)
    #body
  ],
)

#let metric(value, label, note, tone: "blue") = block(
  width: 100%, height: 0.78in,
  fill: panel,
  stroke: (left: 3pt + tone-ink(tone), rest: 0.5pt + rule),
  radius: 4pt, inset: 7pt,
  [
    #text(size: 18pt, weight: "bold", fill: tone-ink(tone))[#value]
    #h(5pt)
    #text(size: 7pt, weight: "bold", fill: navy)[#label]
    #v(1pt)
    #text(size: 6.3pt, fill: muted)[#note]
  ],
)

#let flow-box(title, count, note, tone: "blue") = block(
  width: 100%,
  fill: tone-fill(tone),
  stroke: 0.65pt + tone-ink(tone),
  radius: 4pt,
  inset: 6pt,
  [
    #grid(
      columns: (1fr, auto),
      text(size: 7.2pt, weight: "bold", fill: navy)[#title],
      tag(count, tone: tone),
    )
    #v(2pt)
    #text(size: 6.3pt, fill: ink)[#note]
  ],
)

#let arrow(body: [→]) = align(center + horizon, text(size: 16pt, weight: "bold", fill: blue, body))

#let module-table(group-list) = {
  let rows = evidence.modules.filter(m => group-list.contains(m.group))
  let cells = ()
  for m in rows {
    let tone = ceiling-tone(m.ceiling)
    cells.push(table.cell(fill: tone-fill(tone), [
      #text(size: 6.3pt, weight: "bold", fill: navy)[#m.module]
      #linebreak()
      #tag(m.ceiling, tone: tone)
    ]))
    cells.push(text(size: 6.3pt, m.method))
    cells.push(text(size: 6.3pt, m.data))
    cells.push(text(size: 6.3pt, m.live_use))
  }
  table(
    columns: (1.36fr, 1.62fr, 2.26fr, 1.23fr),
    align: (left, left, left, left),
    table.header(
      repeat: true,
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[MODULE / CEILING]],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[METHOD]],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[DATASET / FIXTURE BINDING]],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[WHAT IT MAY DO NOW]],
    ),
    ..cells,
  )
}

// PAGE 1 — FOUNDER MAP
#page-title(
  "01 / THE OPERATING PICTURE",
  [Data enters many specialist modules. One policy brain decides what may count.],
  [The current system is a governed evidence network—not an authorized ranking engine. Modules emit typed evidence; the central orchestrator applies authority, applicability, evidence strength, and coverage before any output is released.],
)

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  column-gutter: 7pt,
  metric([29], [MODULES MAPPED], [Every live manifest module appears once], tone: "blue"),
  metric([14], [MODULES WITH LOCKS], [37 v2/v3 module-lock files], tone: "green"),
  metric([26], [ACCOUNTED UNITS], [2.304 GiB across v2/v3 manifests], tone: "green"),
  metric([4], [UNACCOUNTED FILES], [409.199 MiB raw and unactivated], tone: "amber"),
)

#v(8pt)
#subsection([HOW THE SUBMODULES INTERACT WITH THE CENTRAL BRAIN])
#v(4pt)
#grid(
  columns: (1.9fr, 0.25fr, 1.05fr, 0.25fr, 2.15fr, 0.25fr, 1.55fr),
  column-gutter: 5pt,
  [
    #flow-box([MOLECULE], [5], [Identity, proposal generation, role, novelty, design gates], tone: "blue")
    #v(4pt)
    #flow-box([FORMULATION], [8], [Arithmetic, universe, ingredients, rules, solvency, tolerance], tone: "blue")
    #v(4pt)
    #flow-box([PERFORMANCE], [4], [Barrier, cure, process QC, viscosity], tone: "blue")
    #v(4pt)
    #flow-box([ASSURANCE], [12], [Contracts, custody, claims, replay, reporting, red-team], tone: "blue")
  ],
  arrow(),
  block(fill: navy2, radius: 4pt, inset: 8pt, [
    #text(size: 7.4pt, weight: "bold", fill: white)[TYPED EVIDENCE BUS]
    #v(6pt)
    #text(size: 7pt, fill: white)[PASS]
    #v(2pt)
    #text(size: 7pt, fill: white)[FAIL]
    #v(2pt)
    #text(size: 7pt, fill: white)[ABSTAIN]
    #v(2pt)
    #text(size: 7pt, fill: white)[NOT_APPLICABLE]
    #v(7pt)
    #text(size: 6.3pt, fill: rgb("#D8E4EF"))[Candidate-bound provenance travels with each result.]
  ]),
  arrow(),
  block(fill: amber-light, stroke: 1pt + amber, radius: 5pt, inset: 9pt, [
    #text(size: 10pt, weight: "bold", fill: amber)[CENTRAL POLICY BRAIN]
    #v(4pt)
    #text(size: 7.2pt, weight: "bold", fill: navy)[optimizer-orchestrator]
    #v(2pt)
    #text(size: 6.3pt)[Reads signed module envelopes and model-card authority. Applies:]
    #v(4pt)
    #text(size: 6.3pt)[• authority ceiling]
    #linebreak()
    #text(size: 6.3pt)[• applicability]
    #linebreak()
    #text(size: 6.3pt)[• evidence strength]
    #linebreak()
    #text(size: 6.3pt)[• coverage + abstention]
    #v(6pt)
    #tag([RANK: NONE], tone: "red")
  ]),
  arrow(),
  block(fill: panel, stroke: 0.7pt + rule, radius: 4pt, inset: 8pt, [
    #text(size: 7.4pt, weight: "bold", fill: navy)[AUTHORIZED OUTPUTS]
    #v(5pt)
    #text(size: 6.3pt)[Audit cohort]
    #linebreak()
    #text(size: 6.3pt)[Reject / quarantine]
    #linebreak()
    #text(size: 6.3pt)[Abstain]
    #linebreak()
    #text(size: 6.3pt)[CRO packet draft]
    #v(7pt)
    #tag([NO FINAL SCORE], tone: "red")
  ]),
)

#v(7pt)
#grid(
  columns: (1.6fr, 5fr),
  column-gutter: 6pt,
  panel-box([MEASURED RETURN], text(size: 6.3pt)[Independent lab result → signed, candidate-bound intake → provenance ledger → eligible module evidence.], tone: "green", height: 0.72in),
  panel-box([ADAPTATION RULE], text(size: 6.3pt)[Only accepted empirical returns may update an authorized method. Claim locks, held-out splits, truth labels, thresholds, and solver authority never adapt silently. Today there is no candidate-bound wet-lab feedback loop in production.], tone: "amber", height: 0.72in),
)

#v(5pt)
#block(fill: navy, radius: 4pt, inset: 7pt, [
  #text(size: 6.3pt, weight: "bold", fill: white)[AUTHORITY LOCK  ]
  #text(size: 6.3pt, fill: white)[INTERESTING_FOR_AUDIT is not a rank. RANK: NONE. FINAL AGGREGATE SCORE: NOT AUTHORIZED. Unknown proposals are unmade digital proposals. Dataset presence is not model validity. No safety, synthesis, procurement, qualification, performance, novelty, or execution claim is authorized.]
])

#pagebreak()

// PAGE 2 — INFRASTRUCTURE
#page-title(
  "02 / ASSURANCE + INFRASTRUCTURE · 12 MODULES",
  [The control plane governs evidence; it does not create scientific truth.],
  [These modules enforce identity, custody, authority, replay, claims, and packaging. Most use deterministic fixtures or ledgers—not scientific training datasets. The central brain is intentionally DISABLED as a scoring objective.],
)

#module-table(("infrastructure",))

#v(6pt)
#grid(
  columns: (1fr, 1fr, 1fr), column-gutter: 6pt,
  panel-box([GREEN / WHAT IS STRONG], text(size: 6.3pt)[Typed contracts, content hashes, evidence custody, replay, claim locks, and fail-closed packaging.], tone: "green"),
  panel-box([AMBER / WHAT DATA MEANS HERE], text(size: 6.3pt)[Fixtures prove deterministic behavior. A module lock proves custody and assignment—not scientific lift.], tone: "amber"),
  panel-box([RED / WHAT IS ABSENT], text(size: 6.3pt)[No infrastructure module may turn a weak scientific signal into rank, novelty, safety, or performance authority.], tone: "red"),
)

#pagebreak()

// PAGE 3 — FORMULATION + PERFORMANCE
#page-title(
  "03 / FORMULATION + PERFORMANCE · 12 MODULES",
  [Useful arithmetic and diagnostics; no validated performance objective.],
  [Eight formulation modules and four performance modules consume a mix of public locks, local fixtures, and quarantined material. CONSTRAINT_ONLY can reject an invalid candidate; AUDIT_ONLY can draw attention; neither can rank.],
)

#module-table(("formulation", "performance"))

#v(6pt)
#grid(
  columns: (1fr, 1fr, 1fr), column-gutter: 6pt,
  panel-box([FORMULATION], text(size: 6.3pt)[Exact arithmetic and signed envelopes can establish internal consistency. They do not establish mixability, cure quality, or coating performance.], tone: "green"),
  panel-box([PERFORMANCE], text(size: 6.3pt)[Public and process datasets support endpoint contracts and offline diagnostics. Public corrosion currently shows no lift versus baseline.], tone: "amber"),
  panel-box([DECISION BOUNDARY], text(size: 6.3pt)[Independent, candidate-bound experiments remain the route to scientific authority. ST-19168 remains untouched and rights-quarantined.], tone: "red"),
)

#pagebreak()

// PAGE 4 — MOLECULE + ACCOUNTED DATA
#page-title(
  "04 / MOLECULE METHODS + ACCOUNTED DOWNLOADS",
  [Molecule models are diagnostic and constraint machinery—not a ranking stack.],
  [Five molecule modules use structural rules, exact/nearest-neighbor checks, fingerprints, ontologies, and deterministic proposal handling. No GNN, neural, or reinforcement-learning method carries authority. Potential novelty is NOT_ESTABLISHED.],
)

#module-table(("molecule",))

#v(7pt)
#subsection([DOWNLOADED AND ACCOUNTED: NORMALIZED MANIFEST + NAMED MODULE LOCK])
#v(4pt)
#table(
  columns: (1.12fr, 2.3fr, 2.55fr),
  align: (left, left, left),
  table.header(
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[SOURCE FAMILY]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[NORMALIZED ACQUISITION UNITS]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[NAMED MODULE CONSUMERS]],
  ),
  [BigSolDB], [density; solubility], [design rule · ingredient library · known answer · solvency · tolerance],
  [CORR-DATA], [database; checksum], [barrier · public corrosion · source ledger],
  [OpenPoly / POINT2], [counts; properties; model results; train/test; run log], [known answer · molecule novelty · molecule property],
  [PolyOmics / PolyVERSE], [small molecules; χ/DMF; sorption; cohesive energy; diffusivity; melt viscosity; thermoset mechanics], [design rule · molecule novelty/property · solvency · viscosity · cure],
  [PI1M / RadonPy / OMG], [structures; PI1070; physical properties], [molecule generator/novelty/property · tolerance · solvency],
  [PURformance / public process], [evaluation; experiment; UCI SECOM; PRONTO], [design rule · process QC],
  [ChEBI], [release 252 3-star], [molecule property],
)

#v(6pt)
#grid(
  columns: (1fr, 1fr, 1fr), column-gutter: 6pt,
  panel-box([26 ACQUISITION RECORDS], text(size: 6.3pt)[20 in v2 + 6 in v3; 2,473,556,779 raw bytes across manifests (2.304 GiB).], tone: "green"),
  panel-box([37 MODULE LOCK FILES], text(size: 6.3pt)[Locks assign accounted units to 14 modules. Several datasets intentionally serve more than one diagnostic.], tone: "green"),
  panel-box([IMPORTANT LIMIT], text(size: 6.3pt)[The bytes total may repeat an upstream package. “Accounted” means normalized and assigned—not trained, validated, or scoring.], tone: "amber"),
)

#pagebreak()

// PAGE 5 — UNACCOUNTED DOWNLOADS
#page-title(
  "05 / RAW DOWNLOADS NOT YET ACCOUNTED FOR",
  [Four files, 409.199 MiB: present on disk, absent from every activated module binding.],
  [“Unaccounted” is precise: raw bytes exist, but there is no normalized manifest and no module-specific lock. Catalog intent is planning metadata only; it does not mean a model currently uses the data.],
)

#table(
  columns: (1.82fr, 0.95fr, 0.7fr, 1.35fr, 1.62fr),
  align: (left, left, right, left, left),
  table.header(
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[RAW FILE / SHA-256]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[ACQUISITION UNIT]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[BYTES]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[CATALOG INTENT]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[WHY NOT ACCOUNTED / ACTIVATED]],
  ),
  [#text(size: 6.3pt, weight: "bold")[feedback/v1/external_data/omg_public_zips/raw/]
   #text(size: 6.3pt)[OMG_monomers_CRU.zip]
   #linebreak()
   #text(font: "DejaVu Sans Mono", size: 6.3pt)[4577e389b4c33e825b2922ee714a21ee]
   #linebreak()
   #text(font: "DejaVu Sans Mono", size: 6.3pt)[f5016ca2d8684c6355aa8d35a5da034f]],
  [omg_structure_reaction],
  [162,475,424],
  [generator: TRAINING_CORPUS; role: DIAGNOSTIC; scoring false],
  [No normalized manifest or module lock. Planned for two molecule modules; currently unused.],

  [#text(size: 6.3pt, weight: "bold")[feedback/v1/external_data/polyuniverse_epoxy/raw/]
   #text(size: 6.3pt)[Epoxy_1M_p.csv]
   #linebreak()
   #text(font: "DejaVu Sans Mono", size: 6.3pt)[9f1f5c593463b9c26a026948901e37b4]
   #linebreak()
   #text(font: "DejaVu Sans Mono", size: 6.3pt)[db545d17f05d5cd80baca5c3e14e0c45]],
  [polyuniverse_pairs],
  [265,396,937],
  [No named consumer],
  [No normalized manifest/module lock; upstream data license unresolved.],

  [#text(size: 6.3pt, weight: "bold")[feedback/v1/external_data/polyuniverse_epoxy/raw/]
   #text(size: 6.3pt)[epoxy_diE.csv]
   #linebreak()
   #text(font: "DejaVu Sans Mono", size: 6.3pt)[14fe4febeb0157470c113634c607bff46]
   #linebreak()
   #text(font: "DejaVu Sans Mono", size: 6.3pt)[f3f0b4fed6376b54e2da8315bfde448]],
  [polyuniverse_epoxides],
  [888,169],
  [No named consumer],
  [No normalized manifest/module lock; upstream data license unresolved.],

  [#text(size: 6.3pt, weight: "bold")[feedback/v1/external_data/polyuniverse_epoxy/raw/]
   #text(size: 6.3pt)[epoxy_diN.csv]
   #linebreak()
   #text(font: "DejaVu Sans Mono", size: 6.3pt)[8bdd4e9416e6805e5cbaa283acabf8a4]
   #linebreak()
   #text(font: "DejaVu Sans Mono", size: 6.3pt)[918f51a95d47768f0e89d05f7b960389]],
  [polyuniverse_amines],
  [315,528],
  [No named consumer],
  [No normalized manifest/module lock; upstream data license unresolved.],
)

#v(7pt)
#grid(
  columns: (1fr, 1fr, 1fr), column-gutter: 6pt,
  panel-box([1 / ACTIVATE DELIBERATELY], text(size: 6.3pt)[For OMG reaction data: confirm rights + exact consumer/method, normalize, create a signed lock, then run leakage and held-out checks.], tone: "amber"),
  panel-box([2 / HOLD POLYUNIVERSE], text(size: 6.3pt)[Keep the three PolyUniverse files quarantined until upstream licensing and derivative rights are resolved and a module owner is named.], tone: "red"),
  panel-box([3 / KEEP AUTHORITY CLOSED], text(size: 6.3pt)[Do not infer use from presence. Do not enable ranking until an independently authorized evidence package and movement receipt exist.], tone: "red"),
)

#v(6pt)
#grid(
  columns: (1fr, 1fr), column-gutter: 6pt,
  panel-box([NOT COUNTED AS DOWNLOADED / UNACCOUNTED], text(size: 6.3pt)[v1 derived polymer_corpus_rows.jsonl is derived and used; PolyOmics PDF/HTML are references; the artifacts tree contains tool/model artifacts.], tone: "blue"),
  panel-box([ORD IS MANIFEST-ONLY], text(size: 6.3pt)[feedback/v4/catalog.json describes 550 ORD objects / 1,181,061,030 bytes, but the corpus is not materialized locally. It is not counted as downloaded data.], tone: "blue"),
)

#v(6pt)
#source-note([Primary evidence: live module manifest be6d3e80…; module inventory 7bf3e74d…; v2 catalog c7ad68a0…; v3 catalog d37ce23b…; v4 catalog bea0d313…. Exact source paths and full SHA-256 values are preserved in evidence-map.json and SHA256SUMS.])
