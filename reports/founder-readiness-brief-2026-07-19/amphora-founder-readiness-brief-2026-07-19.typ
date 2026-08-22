#let snapshot = json("evidence-snapshot.json")

#let navy = rgb("#10243E")
#let navy-2 = rgb("#193653")
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
  title: "Amphora Compound MVP Founder Review — 19 July 2026",
  author: "Amphora",
  date: datetime(year: 2026, month: 7, day: 19),
  keywords: ("Amphora", "founder readiness", "Phase 0", "internal board brief"),
)

#set page(
  paper: "us-letter",
  flipped: true,
  fill: paper,
  margin: (top: 0.58in, bottom: 0.36in, left: 0.44in, right: 0.44in),
  header: context {
    grid(
      columns: (1fr, auto, auto),
      column-gutter: 16pt,
      align: (left, center, right),
      text(size: 6.8pt, weight: "semibold", fill: navy)[AMPHORA / FOUNDER READINESS],
      text(size: 6.5pt, fill: muted)[Internal founder brief · As of 19 July 2026],
      text(size: 6.8pt, weight: "semibold", fill: navy)[PAGE #counter(page).display("1") / 14],
    )
    v(3pt)
    line(length: 100%, stroke: 0.7pt + rule)
  },
  footer: context {
    line(length: 100%, stroke: 0.5pt + rule)
    v(2pt)
    grid(
      columns: (1fr, auto),
      text(size: 5.8pt, fill: muted)[Repository-grounded status brief · not scientific validation, legal opinion, or product-readiness claim],
      text(size: 5.8pt, fill: muted)[Evidence snapshot: amphora.founder-readiness-evidence-snapshot.v1],
    )
  },
)

#set text(font: "Lato", size: 7.8pt, fill: ink, lang: "en")
#set par(leading: 0.52em, justify: false)
#set table(stroke: 0.45pt + rule, inset: (x: 4pt, y: 3pt))

#let tone-fill(tone) = if tone == "green" { green-light } else if tone == "amber" { amber-light } else if tone == "red" { red-light } else { blue-light }
#let tone-ink(tone) = if tone == "green" { green } else if tone == "amber" { amber } else if tone == "red" { red } else { blue }
#let status-tone(status) = if status == "GREEN_SIGNED_PHASE_0" { "green" } else if status == "YELLOW_IMPLEMENTATION_COMPLETE_PROMOTION_UNFINISHED" { "amber" } else { "red" }
#let status-label(status) = if status == "GREEN_SIGNED_PHASE_0" { "● SIGNED P0" } else if status == "YELLOW_IMPLEMENTATION_COMPLETE_PROMOTION_UNFINISHED" { "◆ RELEASE" } else { "■ BLOCKED" }

#let kicker(body) = text(size: 6.2pt, weight: "bold", fill: blue, tracking: 0.08em, body)
#let section-title(body) = text(size: 14.5pt, weight: "bold", fill: navy, body)
#let subsection(body) = text(size: 8.3pt, weight: "bold", fill: navy, body)
#let source-note(body) = text(size: 5.8pt, fill: muted, body)

#let page-title(k, title, dek) = {
  kicker(k)
  v(2pt)
  section-title(title)
  v(2pt)
  text(size: 7.5pt, fill: muted, dek)
  v(8pt)
}

#let chip(status) = {
  let tone = status-tone(status)
  box(
    fill: tone-fill(tone),
    radius: 9pt,
    inset: (x: 5pt, y: 2pt),
    text(size: 6.3pt, weight: "bold", fill: tone-ink(tone), status-label(status)),
  )
}

#let tag(body, tone: "blue") = box(
  fill: tone-fill(tone),
  radius: 7pt,
  inset: (x: 5pt, y: 2pt),
  text(size: 5.9pt, weight: "semibold", fill: tone-ink(tone), body),
)

#let card(value, label, note, tone: "blue") = block(
  width: 100%,
  height: 0.82in,
  fill: panel,
  stroke: (left: 3pt + tone-ink(tone), rest: 0.5pt + rule),
  radius: 4pt,
  inset: 8pt,
  [
    #text(size: 19pt, weight: "bold", fill: tone-ink(tone))[#value]
    #h(5pt)
    #text(size: 7.1pt, weight: "bold", fill: navy)[#label]
    #v(2pt)
    #text(size: 6.2pt, fill: muted)[#note]
  ],
)

#let panel-box(title, body, tone: "blue", height: auto) = block(
  width: 100%,
  height: height,
  fill: panel,
  stroke: 0.6pt + rule,
  radius: 4pt,
  inset: 8pt,
  [
    #text(size: 7.4pt, weight: "bold", fill: tone-ink(tone))[#title]
    #v(4pt)
    #body
  ],
)

#let bullet-line(label, body, tone: "blue") = {
  grid(
    columns: (9pt, 1fr),
    column-gutter: 3pt,
    text(size: 7.5pt, weight: "bold", fill: tone-ink(tone))[•],
    [#text(size: 7.5pt, weight: "semibold", fill: navy)[#label] #text(size: 7.5pt, fill: ink)[#body]],
  )
  v(3pt)
}

#let module-matrix(lanes, compact: false, statuses: none) = {
  let mods = snapshot.modules.filter(m => lanes.contains(m.lane) and (statuses == none or statuses.contains(m.status_color)))
  let cells = ()
  for m in mods {
    let tone = status-tone(m.status_color)
    cells.push(table.cell(fill: tone-fill(tone), [
      #text(size: 6.3pt, weight: "bold", fill: navy)[#m.module_id]
      #linebreak()
      #text(size: 6.3pt, fill: muted)[#m.display_name]
    ]))
    cells.push(text(size: 6.3pt, m.purpose))
    cells.push(table.cell(align: center + horizon, [#chip(m.status_color) #linebreak() #text(size: 6.3pt, fill: muted)[#m.live_phase]]))
    cells.push(text(size: 6.3pt, m.current_kpi_or_diagnostic))
    cells.push(text(size: 6.3pt, m.main_blocker))
    cells.push(text(size: 6.3pt, m.next_action))
  }
  table(
    columns: (1.46fr, 1.34fr, 0.79fr, 1.45fr, 1.44fr, 1.42fr),
    align: (left, left, center, left, left, left),
    table.header(
      repeat: true,
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[MODULE]],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[PURPOSE]],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[LIVE STATUS]],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[EVIDENCE / KPI]],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[DECISIVE BLOCKER]],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[NEXT ACTION]],
    ),
    ..cells,
  )
}

#let metric-pill(value, label, tone: "blue") = block(
  fill: tone-fill(tone),
  radius: 3pt,
  inset: (x: 5pt, y: 4pt),
  align(center, [
    #text(size: 10.5pt, weight: "bold", fill: tone-ink(tone))[#value]
    #linebreak()
    #text(size: 5.7pt, weight: "semibold", fill: ink)[#label]
  ]),
)

// PAGE 1 — FOUNDER DASHBOARD
#page-title(
  "01 / FOUNDER DASHBOARD",
  [A credible control spine. Scientific authority remains at zero.],
  [The signed truth is 8 of 29 modules at Phase 0. Four compound modules are milestone movement targets; 12 of 29 is only a conditional outcome after campaign evidence, credentialed evaluation, independent review, and four atomic movements.],
)

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  column-gutter: 7pt,
  card([8 / 29], [LIVE PHASE 0], [Signed deterministic controls], tone: "green"),
  card([4], [MOVEMENT TARGETS], [All remain pre-Phase-0 today], tone: "amber"),
  card([21], [PRE-PHASE-0], [Science, data, rights, lab, or external closure], tone: "red"),
  card([0], [PHASE 1 / 2], [No module has independent higher-phase validation], tone: "red"),
)

#v(8pt)
#grid(
  columns: (8fr, 4fr, 17fr),
  gutter: 0pt,
  block(height: 10pt, fill: green, radius: (left: 5pt)),
  block(height: 10pt, fill: amber),
  block(height: 10pt, fill: red, radius: (right: 5pt)),
)
#v(3pt)
#grid(
  columns: (8fr, 4fr, 17fr),
  text(size: 6pt, weight: "semibold", fill: green)[● 8 signed Phase 0],
  align(center)[#text(size: 6pt, weight: "semibold", fill: amber)[◆ 4 compound movement targets]],
  align(right)[#text(size: 6pt, weight: "semibold", fill: red)[■ 21 pre-Phase-0 modules]],
)

#v(8pt)
#grid(
  columns: (1fr, 1fr),
  column-gutter: 8pt,
  panel-box([WHAT IS REAL], [
    #bullet-line([Trust spine.], [Typed candidate identity, source custody, intake, authority, packaging, provenance, and red-team controls are signed.], tone: "green")
    #bullet-line([Deterministic enforcement.], [Malformed, unsupported, tampered, or unauthorized inputs fail closed.], tone: "green")
    #bullet-line([Operational shell.], [Native dispatch, parallel scoring, lineage, replay, resume/export, and telemetry run.], tone: "green")
    #bullet-line([Current data.], [30 rights-known public-corrosion CSVs and six public coating systems are available.], tone: "green")
  ], tone: "green", height: 1.60in),
  panel-box([WHAT IS NOT YET PROVEN], [
    #bullet-line([Scientific model.], [No endpoint model or baseline lift has independent validation.], tone: "red")
    #bullet-line([Ranking objective.], [All 29 modules remain non-ranking; scientific objective count is zero.], tone: "red")
    #bullet-line([Laboratory result.], [No owned candidate-bound wet-lab result exists; the CRO packet says NOT_EXECUTED.], tone: "red")
    #bullet-line([Product claim.], [No qualification, procurement, legal, freedom-to-operate, safety, or product-performance authority exists.], tone: "red")
  ], tone: "red", height: 1.60in),
)

#v(8pt)
#subsection([FIVE FOUNDER DECISIONS NOW])
#v(4pt)
#grid(
  columns: (1fr, 1fr, 1fr, 1fr, 1fr),
  column-gutter: 5pt,
  panel-box([1 / CREDENTIALS], text(size: 5.9pt)[Authorize distinct external evaluator and reviewer signers.], tone: "amber", height: 0.65in),
  panel-box([2 / RELEASE], text(size: 5.9pt)[Fund the four-module campaign → evaluation → review → movement sequence.], tone: "amber", height: 0.65in),
  panel-box([3 / COUNTERPARTIES], text(size: 5.9pt)[Contract lab, statistician, chemistry labeling, curation, and counsel.], tone: "amber", height: 0.65in),
  panel-box([4 / DATA], text(size: 5.9pt)[Buy owned, candidate-bound measurements with custody and rights.], tone: "amber", height: 0.65in),
  panel-box([5 / AUTHORITY], text(size: 5.9pt)[Keep ranking and chemistry-changing mutation disabled until promotion.], tone: "amber", height: 0.65in),
)

#v(5pt)
#block(
  width: 100%, fill: navy, radius: 4pt, inset: 7pt,
  [#text(size: 6.3pt, weight: "bold", fill: white)[AUTHORITY LOCK] #h(7pt) #text(size: 6.3pt, fill: white)[INTERESTING_FOR_AUDIT is not a rank. RANK: NONE. FINAL AGGREGATE SCORE: NOT AUTHORIZED. Potential novelty is NOT_ESTABLISHED. Unknown proposals are unmade digital proposals. No safety, synthesis, procurement, qualification, performance, or execution claim is authorized.]],
)
#v(4pt)
#source-note([Authority: live v2 decision report. Green means signed deterministic Phase 0, not scientific validity. Yellow is PRE_PHASE_0 today.])

#pagebreak()

// PAGE 2 — EVIDENCE LADDER AND READINESS MODEL
#page-title(
  "02 / EVIDENCE LADDER + READINESS MODEL",
  [A signed control is not scientific validation—and neither authorizes a product.],
  [Implemented controls prove narrow enforcement. Scientific validation requires locked external evidence. Product authority requires prospective, product-relevant evidence and explicit scope. Current phase comes only from signed movement.],
)

#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  column-gutter: 6pt,
  panel-box([PRE-PHASE 0 / NOT YET AUTHORIZED], text(size: 6.2pt)[Code or artifacts may exist, but required evaluation, review, rights, benchmark, or movement gates remain incomplete.], tone: "red", height: 0.82in),
  panel-box([PHASE 0 / USEFUL CONTROL], text(size: 6.2pt)[Signed validator or enforcement capability inside a narrow applicability domain. Scientific outcome may be NOT_APPLICABLE.], tone: "green", height: 0.82in),
  panel-box([PHASE 1 / INDEPENDENT EVIDENCE], text(size: 6.2pt)[A locked external benchmark passes under independent evaluation and review within a signed domain. Current count: 0.], tone: "blue", height: 0.82in),
  panel-box([PHASE 2 / PRODUCT EVIDENCE], text(size: 6.2pt)[Prospective, product-relevant validation and authority beyond a bounded research claim. Current count: 0.], tone: "blue", height: 0.82in),
)

#v(8pt)
#grid(
  columns: (1.03fr, 1fr),
  column-gutter: 8pt,
  [
    #subsection([PORTFOLIO MAP / MODULE COUNTS])
    #v(4pt)
    #table(
      columns: (1.4fr, 0.8fr, 0.8fr, 0.8fr, 0.8fr),
      align: (left, center, center, center, center),
      table.header(
        table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[LANE]],
        table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[TOTAL]],
        table.cell(fill: green-light)[#text(size: 6pt, weight: "bold", fill: green)[● SIGNED]],
        table.cell(fill: amber-light)[#text(size: 6pt, weight: "bold", fill: amber)[◆ RELEASE]],
        table.cell(fill: red-light)[#text(size: 6pt, weight: "bold", fill: red)[■ BLOCKED]],
      ),
      [Infrastructure], [12], [7], [0], [5],
      [Formulation], [8], [0], [0], [8],
      [Performance], [4], [0], [0], [4],
      [Molecule], [5], [1], [0], [4],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[TOTAL]],
      table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[29]],
      table.cell(fill: green)[#text(size: 6.3pt, weight: "bold", fill: white)[8]],
      table.cell(fill: amber)[#text(size: 6.3pt, weight: "bold", fill: white)[0]],
      table.cell(fill: red)[#text(size: 6.3pt, weight: "bold", fill: white)[21]],
    )
  ],
  panel-box([EVIDENCE CONTRACT], [
    #bullet-line([Live phase authority.], [phase0-decision-report.v2.json], tone: "blue")
    #bullet-line([Ceilings.], [Current 29-module manifest: 14 disabled, 10 audit-only, 5 constraint-only; 0 ranking-eligible.], tone: "blue")
    #bullet-line([KPIs.], [Capability profiles plus hash-bound benchmark artifacts.], tone: "blue")
    #bullet-line([Plans.], [Program work orders and preregistration; always labeled PLANNED NOT EXECUTED.], tone: "blue")
    #bullet-line([No override.], [Stale profile phases and narrative summaries cannot change the live decision.], tone: "blue")
  ], tone: "blue", height: 1.68in),
)

#v(8pt)
#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 7pt,
  panel-box([ENGINEERING EVIDENCE / VALIDATED CONTROLS], [
    #text(size: 17pt, weight: "bold", fill: green)[30,000]
    #text(size: 6.2pt, weight: "semibold", fill: navy)[ certified red-team negatives]
    #v(3pt)
    #text(size: 6.2pt)[Two byte-identical locked replays; signed evaluation and independent review.]
    #v(5pt)
    #text(size: 12pt, weight: "bold", fill: amber)[5 suites · 9+ / 44−]
    #v(2pt)
    #text(size: 6.2pt)[Implementation-complete release diagnostics; authority ceilings unchanged.]
  ], tone: "green", height: 1.88in),
  panel-box([DATA TRUTH / CURRENT INVENTORY], [
    #grid(columns: (1fr, 1fr), metric-pill([30], [RIGHTS-KNOWN CSVs], tone: "blue"), metric-pill([6], [PUBLIC SYSTEMS], tone: "blue"))
    #v(5pt)
    #bullet-line([Excluded.], [Rights-unresolved material is quarantined from ranking and promotion evidence.], tone: "red")
    #bullet-line([Owned wet lab.], [0 candidate-bound results.], tone: "red")
    #bullet-line([Claim limit.], [Local presence is not ownership, permission, or scientific validity.], tone: "red")
  ], tone: "blue", height: 1.88in),
  panel-box([SCIENTIFIC SIGNALS / NOT VALIDATED], [
    #text(size: 6.4pt, weight: "bold", fill: navy)[PUBLIC CORROSION]
    #v(2pt)
    #text(size: 11.5pt, weight: "bold", fill: red)[0.666667 = 0.666667]
    #text(size: 5.9pt)[ model = baseline · absolute lift 0]
    #v(5pt)
    #text(size: 6.4pt, weight: "bold", fill: navy)[CURE EXPLORATORY AUDIT]
    #v(2pt)
    #text(size: 11.5pt, weight: "bold", fill: amber)[0.4375 vs 0.375]
    #text(size: 5.9pt)[ lift 0.0625 · below locked requirements]
    #v(5pt)
    #text(size: 6pt)[Known answers: 13 verified + 1 unverified historical; arithmetic is a distinct 6/6 subset.]
  ], tone: "red", height: 1.88in),
)

#v(5pt)
#source-note([Every figure above is classified in the evidence snapshot as validated control, current checked artifact, exploratory result, or inventory fact.])

#pagebreak()

// PAGE 3 — SIGNED TRUST SPINE
#page-title(
  "03 / SIGNED TRUST SPINE",
  [Seven controls make evidence tamper-evident, replayable, and claim-bounded.],
  [These are the existing signed Phase-0 infrastructure controls. They establish a deterministic custody and policy spine—not formulation fitness, scientific validity, or product authority.],
)

#module-matrix(("infrastructure",), compact: true, statuses: ("GREEN_SIGNED_PHASE_0",))

#v(7pt)
#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 6pt,
  panel-box([IDENTITY + CUSTODY], text(size: 6.3pt)[Candidate contract, evidence intake, source ledger, and run provenance bind identity, observed bytes, rights context, and replay lineage.], tone: "green", height: 0.78in),
  panel-box([AUTHORITY + ADVERSARIAL CONTROL], text(size: 6.3pt)[Model-card authority and signed red-team audit reject escalation, laundering, spoofing, and out-of-scope use.], tone: "green", height: 0.78in),
  panel-box([FAIL-CLOSED REPORTING], text(size: 6.3pt)[The report packager binds evidence to claims and preserves explicit abstention, negative results, and claim locks.], tone: "green", height: 0.78in),
)

#v(4pt)
#source-note([Signed Phase 0 means useful deterministic control inside a narrow applicability domain. The scientific outcome for these controls is NOT_APPLICABLE.])

#pagebreak()

// PAGE 4 — REMAINING INFRASTRUCTURE AND TRANSFER
#page-title(
  "04 / REMAINING INFRASTRUCTURE + TRANSFER",
  [Five modules still depend on external evidence, rights, or execution.],
  [They are PRE_PHASE_0. Code and fixtures cannot substitute for a laboratory return, an independent benchmark, counsel-defined scope, supplier records, or an explicitly authorized scientific objective.],
)

#module-matrix(("infrastructure",), compact: true, statuses: ("RED_SUBSTANTIVE_CLOSURE_REQUIRED",))

#v(7pt)
#subsection([TRANSFER PATH / WHERE AUTHORITY STOPS])
#v(4pt)
#grid(
  columns: (1fr, auto, 1fr, auto, 1fr, auto, 1fr, auto, 1fr),
  column-gutter: 3pt,
  panel-box([1 / CANDIDATE-BOUND DRAFT], text(size: 6.3pt)[Protocol packet; execution_authorized: false], tone: "blue", height: 0.68in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([2 / EXTERNAL EXECUTION], text(size: 6.3pt)[Contract lab, method, custody, deviations], tone: "red", height: 0.68in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([3 / SIGNED RETURN], text(size: 6.3pt)[Candidate-bound raw data + uncertainty], tone: "red", height: 0.68in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([4 / INDEPENDENT REVIEW], text(size: 6.3pt)[Distinct signer checks method and scope], tone: "red", height: 0.68in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([5 / POLICY DECISION], text(size: 6.3pt)[No movement unless every gate passes], tone: "amber", height: 0.68in),
)

#v(7pt)
#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 6pt,
  panel-box([CRO PACKAGER], text(size: 6.3pt)[Can bind a protocol to candidate identity. No laboratory result exists; status remains NOT_EXECUTED.], tone: "red", height: 0.72in),
  panel-box([OPTIMIZER], text(size: 6.3pt)[No ranking-eligible module exists. Scientific objectives, optimizer-usable scores, and final aggregate scores remain zero or unauthorized.], tone: "red", height: 0.72in),
  panel-box([RIGHTS + TRANSFER], text(size: 6.3pt)[FTO, sourcing, environment/health/safety, procurement, and known-answer authority require scoped external closure.], tone: "red", height: 0.72in),
)

#v(4pt)
#source-note([Boundary: a packet is not execution; a benchmark fixture is not independent validation; a similarity observation is not novelty or FTO.])

#pagebreak()

// PAGE 5 — FORMULATION
#page-title(
  "05 / FORMULATION SUBMODELS",
  [Arithmetic and boundary controls work. Formulation fitness does not yet exist.],
  [All eight formulation modules. Yellow controls are implementation-complete but remain PRE_PHASE_0; red outputs are audit or constraint-only.],
)

#module-matrix(("formulation",), compact: false)

#v(7pt)
#subsection([BOUNDARY OF PROOF])
#v(4pt)
#grid(
  columns: (1fr, 1fr, 1fr, 1fr),
  column-gutter: 6pt,
  panel-box([ARITHMETIC / KNOWN ANSWER], [
    #text(size: 13pt, weight: "bold", fill: amber)[110 g + 40 g = 150 g]
    #v(3pt)
    #text(size: 5.9pt)[Proves exact mass accounting only; evaluation signature is absent on the current reissue.]
  ], tone: "amber", height: 1.05in),
  panel-box([UNIVERSE / KNOWN ANSWER], [
    #text(size: 13pt, weight: "bold", fill: amber)[3 × 2 × 2 = 12]
    #v(3pt)
    #text(size: 5.9pt)[10 solved + 2 declaratively infeasible. “Solved” is accounting, not scientific feasibility.]
  ], tone: "amber", height: 1.05in),
  panel-box([ENVELOPES / ENFORCEMENT], [
    #text(size: 13pt, weight: "bold", fill: amber)[2+ / 9−]
    #v(3pt)
    #text(size: 5.9pt)[Boundary fixtures prove arithmetic and inclusive-margin enforcement; they do not prove performance.]
  ], tone: "amber", height: 1.05in),
  panel-box([PUBLIC CORROSION / NO LIFT], [
    #text(size: 13pt, weight: "bold", fill: red)[Δ = 0]
    #v(3pt)
    #text(size: 5.9pt)[Model and baseline both 0.666667. No candidate binding or independent validation.]
  ], tone: "red", height: 1.05in),
)

#v(4pt)
#source-note([Solvency, design-rule, ingredient, and tolerance outputs remain constraint or audit signals. None is an authorized objective.])

#pagebreak()

// PAGE 6 — PERFORMANCE + MOLECULE
#page-title(
  "06 / PERFORMANCE + MOLECULE",
  [Executable diagnostics are not scientific authority.],
  [Four performance and five molecule modules. The only signed module here is the deterministic molecule design gate.],
)

#subsection([PERFORMANCE / 4 MODULES])
#v(3pt)
#module-matrix(("performance",), compact: true)

#v(7pt)
#subsection([MOLECULE / 5 MODULES])
#v(3pt)
#module-matrix(("molecule",), compact: true)

#v(7pt)
#grid(
  columns: (1.52fr, 1fr),
  column-gutter: 7pt,
  panel-box([SEVEN BOUNDED PHASE-1 ATTEMPT CANDIDATES], [
    #tag([barrier corrosion], tone: "red") #h(3pt)
    #tag([cure / pot-life], tone: "red") #h(3pt)
    #tag([molecule property], tone: "red") #h(3pt)
    #tag([molecule role], tone: "red") #h(3pt)
    #tag([public corrosion], tone: "red") #h(3pt)
    #tag([solvency], tone: "red") #h(3pt)
    #tag([viscosity], tone: "red")
    #v(5pt)
    #text(size: 5.9pt)[“Attempt” means a preregistered opportunity to produce independent evidence. Completing a campaign does not promise promotion.]
  ], tone: "red", height: 0.90in),
  panel-box([SEPARATE OPERATIONAL CAMPAIGNS], [
    #tag([molecule generator], tone: "amber") #h(4pt) #tag([process-QC twin], tone: "amber")
    #v(5pt)
    #text(size: 5.9pt)[These are operating campaigns, not Phase-1 scientific claims. Generator mutation is not chemistry-changing today.]
  ], tone: "amber", height: 0.90in),
)

#v(4pt)
#source-note([Cure’s 0.0625 exploratory lift is below locked promotion requirements. Public corrosion has zero lift. Both remain unvalidated.])

#pagebreak()

// PAGE 7 — DATA + PHASE-1 PATHWAY
#page-title(
  "07 / 90-DAY EVIDENCE PROGRAM",
  [The 90-day program is preregistered — and has not been executed.],
  [Spend is justified only if it produces owned, candidate-bound raw evidence with custody, rights, locked analysis, and independent signatures.],
)

#block(
  width: 100%, fill: amber-light, stroke: 1pt + amber, radius: 4pt, inset: 7pt,
  [#text(size: 7.2pt, weight: "bold", fill: amber)[PLANNED · NOT EXECUTED] #h(8pt) #text(size: 6.7pt)[No promotion is promised by completing a campaign. Passing the preregistered gates, independent evaluation, review, and signed movement are all still required.]],
)

#v(7pt)
#grid(
  columns: (1fr, 1fr, 1fr, 1fr, 1fr, 1fr),
  column-gutter: 5pt,
  metric-pill([30 / 3], [FORMULATIONS / FAMILIES], tone: "blue"),
  metric-pill([36], [PRIMARY CURE RUNS], tone: "blue"),
  metric-pill([288], [VISCOSITY / SAG CELLS], tone: "blue"),
  metric-pill([210 / 40], [PANELS / SYSTEMS], tone: "blue"),
  metric-pill([96 + 32], [ATTACKS + CONTROLS], tone: "blue"),
  metric-pill([≥ 300], [ELIGIBLE STRUCTURES], tone: "blue"),
)

#v(8pt)
#grid(
  columns: (1.15fr, 1fr),
  column-gutter: 8pt,
  [
    #subsection([CAMPAIGN DESIGN / LOCKED COUNTS])
    #v(4pt)
    #table(
      columns: (1.14fr, 0.78fr, 2.1fr),
      table.header(
        table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[CAMPAIGN]],
        table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[PLANNED N]],
        table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[DECISIVE DESIGN FEATURE]],
      ),
      [Formulation coverage], [30], [Three families; seeded maximin selection without endpoint labels or model ranks.],
      [Cure / application life], [36], [24 fit runs + 12 sealed primary holdouts; external method comparability.],
      [Viscosity / sag], [288 cells], [Three temperatures; apparent viscosity, Krebs units, and sag endpoints.],
      [Barrier corrosion], [210 panels], [40 systems, including 10 untouched external systems; day-56 endpoints.],
      [Independent red team], [96 + 32], [96 planned attacks plus 32 valid controls across 16 families.],
      [Molecule property], [≥ 300], [Deduplicated eligible structures; exact toolkit, identity, formula, mass, and rights reconciliation.],
    )
  ],
  [
    #subsection([COUNTERPARTY DEPENDENCIES])
    #v(4pt)
    #grid(
      columns: (1fr, 1fr),
      column-gutter: 5pt,
      panel-box([INDEPENDENT EVALUATOR], text(size: 5.9pt)[Executes locked analysis and signs results.], tone: "blue", height: 0.56in),
      panel-box([INDEPENDENT REVIEWER], text(size: 5.9pt)[Different trusted signer; checks method and claims.], tone: "blue", height: 0.56in),
      panel-box([CONTRACT LABORATORY], text(size: 5.9pt)[Returns raw candidate-bound data and custody records.], tone: "blue", height: 0.56in),
      panel-box([STATISTICIAN], text(size: 5.9pt)[Maintains splits, intervals, and preregistered gates.], tone: "blue", height: 0.56in),
      panel-box([CHEMISTRY LABELING], text(size: 5.9pt)[Produces blinded role and applicability labels.], tone: "blue", height: 0.56in),
      panel-box([DATA CURATION], text(size: 5.9pt)[Resolves identity, units, rights, and deduplication.], tone: "blue", height: 0.56in),
      panel-box([COUNSEL], text(size: 5.9pt)[Bounds rights, IP, and freedom-to-operate conclusions.], tone: "blue", height: 0.56in),
      panel-box([FOUNDER / OWNER], text(size: 5.9pt)[Protects claim ceilings and stops failed campaigns.], tone: "blue", height: 0.56in),
    )
  ],
)

#v(8pt)
#grid(
  columns: (1fr, 1fr),
  column-gutter: 7pt,
  panel-box([PROMOTION GATE], text(size: 6.1pt)[Raw evidence is complete and rights-eligible; split and benchmark locks match; predefined thresholds pass; evaluator and reviewer are distinct trusted signers; claim locks remain intact; one valid movement event exists.], tone: "green", height: 0.7in),
  panel-box([KILL / HOLD GATE], text(size: 6.1pt)[Stop or hold on rights failure, custody break, split leakage, method mismatch, insufficient sample, baseline non-superiority, confidence interval failure, signer conflict, or any pressure to broaden the applicability domain.], tone: "red", height: 0.7in),
)

#pagebreak()

// PAGE 8 — EVOLUTIONARY ENGINE
#page-title(
  "08 / EVOLUTIONARY ENGINE",
  [Deterministic generation can be governed. Selection remains disabled.],
  [The current molecule demo executes a replayable four-submodel path. The compound-campaign contract separately requires ordered requests, retained rejects and duplicates, one typed outcome from every module per card, signed lineage, and no rank.],
)

#subsection([COMPOUND GENERATION CONTRACT / CURRENT AUTHORITY])
#v(4pt)
#grid(
  columns: (1fr, auto, 1fr, auto, 1fr, auto, 1fr, auto, 1fr, auto, 1fr),
  column-gutter: 3pt,
  panel-box([1 / LOCKED REQUESTS], text(size: 6.3pt)[Family, parents, role, seed, request ID], tone: "blue", height: 0.68in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([2 / GENERATION], text(size: 6.3pt)[Deterministic order; retain reject + duplicate], tone: "amber", height: 0.68in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([3 / 29 OUTCOMES], text(size: 6.3pt)[PASS / FAIL / ABSTAIN / NOT_APPLICABLE], tone: "blue", height: 0.68in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([4 / POLICY SOLVER], text(size: 6.3pt)[Authority + applicability + coverage], tone: "amber", height: 0.68in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([5 / NO SELECTION], text(size: 6.3pt)[RANK: NONE; aggregate unauthorized], tone: "red", height: 0.68in),
  align(center + horizon)[#text(size: 13pt, weight: "bold", fill: blue)[→]],
  panel-box([6 / LINEAGE + REPLAY], text(size: 6.3pt)[JCS hashes, event chain, resume, export], tone: "green", height: 0.68in),
)

#v(8pt)
#grid(
  columns: (1.25fr, 1fr),
  column-gutter: 8pt,
  [
    #subsection([OPERATIONAL CAPABILITIES])
    #v(4pt)
    #grid(
      columns: (1fr, 1fr, 1fr),
      column-gutter: 5pt,
      panel-box([DETERMINISTIC SEEDS], text(size: 6.3pt)[Repeatable request and run identity.], tone: "green", height: 0.54in),
      panel-box([TYPED ATTEMPTS], text(size: 6.3pt)[Accept, reject, negative, duplicate.], tone: "green", height: 0.54in),
      panel-box([MODULE CONTRACT], text(size: 6.3pt)[Exactly 29 unique outcomes per card.], tone: "green", height: 0.54in),
      panel-box([PROVENANCE], text(size: 6.3pt)[Manifest, inputs, outputs, hashes.], tone: "green", height: 0.54in),
      panel-box([REPLAY + RESUME], text(size: 6.3pt)[Snapshots, event chain, export.], tone: "green", height: 0.54in),
      panel-box([LIVE TELEMETRY], text(size: 6.3pt)[Throughput, workers, status, lineage.], tone: "green", height: 0.54in),
    )
  ],
  panel-box([BOUNDED DEMONSTRATION RECEIPT], [
    #grid(
      columns: (1fr, 1fr, 1fr, 1fr, 1fr),
      column-gutter: 3pt,
      metric-pill([3], [POPULATION], tone: "blue"),
      metric-pill([1], [GENERATION], tone: "blue"),
      metric-pill([2], [WORKERS], tone: "blue"),
      metric-pill([6], [ATTEMPTED], tone: "blue"),
      metric-pill([6], [VALID], tone: "blue"),
    )
    #v(4pt)
    #grid(
      columns: (1fr, 1fr, 1fr, 1fr, 1fr),
      column-gutter: 3pt,
      metric-pill([6], [SCORED], tone: "blue"),
      metric-pill([0], [FAILURES], tone: "green"),
      metric-pill([0], [RANKED], tone: "red"),
      metric-pill([0], [OBJECTIVES], tone: "red"),
      metric-pill([0], [SOLUTIONS], tone: "red"),
    )
  ], tone: "blue", height: 1.42in),
)

#v(8pt)
#grid(
  columns: (1fr, 1fr),
  column-gutter: 7pt,
  panel-box([EXPLICIT LIMITATIONS / CURRENT], [
    #bullet-line([Lane.], [The bounded demo runs the molecule lane; formulation is inspect-only.], tone: "red")
    #bullet-line([Generation.], [No locked-grammar unknown exists; chemistry change remains QUARANTINED_NO_STRUCTURE_CHANGE.], tone: "red")
    #bullet-line([Outcome.], [NO_ELIGIBLE_OBJECTIVES is correct under the signed zero-ranking policy.], tone: "red")
    #bullet-line([Dashboard.], [Role-fit and novelty fields are declarations, not authorized objectives.], tone: "red")
  ], tone: "red", height: 1.52in),
  panel-box([ACTIVATION GATE / FUTURE], [
    #bullet-line([Scientific promotion.], [A named module must independently pass its locked benchmark in a signed domain.], tone: "amber")
    #bullet-line([Objective authority.], [The manifest and model card must explicitly authorize use after promotion.], tone: "amber")
    #bullet-line([Chemistry mutation.], [A structure-changing operator needs validation, quarantine policy, and synthesis constraints.], tone: "amber")
    #bullet-line([Replay.], [Authority hashes, evidence, selection, and lineage must remain reproducible.], tone: "amber")
  ], tone: "amber", height: 1.52in),
)

#v(5pt)
#block(width: 100%, fill: navy, radius: 4pt, inset: 7pt, [#text(size: 7pt, weight: "bold", fill: white)[OVERALL ENGINE STATUS] #h(8pt) #text(size: 6.6pt, fill: white)[Yellow operational shell with a red scientific activation gate. The current no-rank outcome demonstrates policy enforcement, not optimization quality.]])

#pagebreak()

#import "compound-mvp-pages.typ": compound-mvp-pages
#compound-mvp-pages(
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
)

#pagebreak()

// PAGE 14 — FOUNDER ACTIONS
#page-title(
  "14 / FOUNDER ACTIONS + DECISION GATES",
  [Spend should purchase independent evidence and owned data.],
  [Do not fund additional unvalidated ranking logic while the existing authority, data, and external-evidence gates remain open.],
)

#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 7pt,
  panel-box([0–30 DAYS / RELEASE + CONTRACT], [
    #bullet-line([Credentials.], [Obtain authorized external evaluator and reviewer credentials.], tone: "amber")
    #bullet-line([Four targets.], [Complete campaign → evaluation → independent review → movement for property, generator, arithmetic, and CRO packaging.], tone: "amber")
    #bullet-line([Trajectory.], [Verify one event per module; projected 12/29 only after success, not current.], tone: "amber")
    #bullet-line([Counterparties.], [Contract lab, statistician, labeling, curation, and counsel.], tone: "amber")
  ], tone: "amber", height: 1.96in),
  panel-box([31–90 DAYS / EXECUTE], [
    #bullet-line([Laboratory.], [Run cure, rheology/sag, solvency, and barrier campaigns.], tone: "blue")
    #bullet-line([Data.], [Execute public-corrosion, molecule-property, and role-label work orders.], tone: "blue")
    #bullet-line([Custody.], [Collect raw candidate-bound evidence with identity, rights, and source lineage.], tone: "blue")
    #bullet-line([Stops.], [Enforce preregistered kill gates without scope broadening.], tone: "blue")
  ], tone: "blue", height: 1.96in),
  panel-box([90+ DAYS / DECIDE], [
    #bullet-line([Benchmarks.], [Run locked independent evaluations and distinct-signer reviews.], tone: "green")
    #bullet-line([Promotion.], [Move only passing modules inside signed applicability domains.], tone: "green")
    #bullet-line([Objectives.], [Activate ranking only after explicit module authority exists.], tone: "green")
    #bullet-line([Mutation.], [Enable chemistry change only after validated operator and safety gates.], tone: "green")
  ], tone: "green", height: 1.96in),
)

#v(8pt)
#subsection([FOUNDER DECISION TABLE])
#v(4pt)
#table(
  columns: (1.22fr, 0.75fr, 1.35fr, 0.58fr, 1.36fr, 1.3fr, 1.05fr),
  table.header(
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[DECISION]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[OWNER]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[DEPENDENCY]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[COST]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[SUCCESS SIGNAL]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[KILL CRITERION]],
    table.cell(fill: navy)[#text(size: 6.3pt, weight: "bold", fill: white)[AUTHORITY GAINED]],
  ),
  [Authorize four-module compound release], [Founder / security], [Distinct trusted evaluator + reviewer], [LOW], [Four valid evaluations, reviews, and one movement each], [Signer conflict, hash drift, or claim-lock change], [Projected 12/29 Phase 0 — only after movement],
  [Contract coatings laboratory], [Science lead], [Method-comparable lab + statistician], [HIGH], [Complete raw cure, rheology, solvency, and barrier evidence], [Custody break, rights failure, method mismatch, or sample shortfall], [No automatic gain; evidence eligible for locked evaluation],
  [Acquire molecule evidence], [Chemistry lead], [Data curator, exact toolkit reproducer, labelers], [MED], [≥300 eligible property structures + blinded role labels], [Identity mismatch, rights gap, leakage, or toolkit drift], [No automatic gain; bounded Phase-1 attempt evidence],
  [Commission rights / legal closure], [Operations + counsel], [Supplier, procurement, environment/health/safety and IP records], [MED], [Signed, scoped rights and legal conclusions], [Unbounded opinion, stale sources, or unresolved jurisdiction], [Audit / decision authority only within signed scope],
  [Hold ranking activation], [Founder / model authority], [Passing independent benchmark + updated signed manifest], [LOW], [At least one explicitly authorized objective in a signed domain], [Any pressure to infer authority from code, tests, or demo], [Objective use only for the promoted module and domain],
)

#v(8pt)
#grid(
  columns: (1.2fr, 1fr),
  column-gutter: 7pt,
  panel-box([EXACT MVP ACCEPTANCE SIGNAL], text(size: 6.3pt)[One hash-bound replay recovers all four known controls; records at least one valid unmade proposal from each authorized reaction family with complete lineage and 29 typed outcomes; retains rejects and duplicates; ingests one independently measured, signed, candidate-bound return; and emits RANK: NONE with FINAL AGGREGATE SCORE: NOT AUTHORIZED.], tone: "green", height: 0.92in),
  panel-box([KILL / HOLD CRITERIA], text(size: 6.3pt)[Stop on toolchain or replay mismatch, known-control miss, unsupported lineage, missing family coverage, rights or custody failure, held-out leakage, signer conflict, baseline non-superiority, hidden rank, aggregate-score injection, or pressure to broaden the signed domain.], tone: "red", height: 0.92in),
)

#v(6pt)
#source-note([Funding rule: purchase independent evidence and owned data—not additional unvalidated ranking logic. No promotion, product claim, or chemistry-changing mutation without the exact signed gate.])
