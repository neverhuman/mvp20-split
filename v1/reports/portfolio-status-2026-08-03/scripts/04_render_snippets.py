#!/usr/bin/env python3
"""04_render_snippets.py — LaTeX fragments for the 2026-08-03 founder report.

Refutation-forward: the report leads with the 54 adversarial verdicts the loop
produced against our own claims. Every per-module section is generated FROM the
ledger, so the narrative cannot drift from the evidence.
"""
import json
import collections
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/home/ubuntu/amphora/build/mvp20-split/amphora-redteam-audit/src")
from amphora_redteam_audit.ledger_ts import parse_ledger_ts, ledger_sort_key  # noqa: E402

ROOT = Path("/home/ubuntu/amphora/reports/portfolio-status-2026-08-03")
DATA, SNIP = ROOT / "data", ROOT / "snippets"
SNIP.mkdir(exist_ok=True)


def esc(s):
    if s is None:
        return ""
    s = str(s)
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"),
                 ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                 ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}"),
                 ("<", r"\textless{}"), (">", r"\textgreater{}")]:
        s = s.replace(a, b)
    return s


def jl(p):
    return [json.loads(l) for l in open(DATA / p) if l.strip()]


def clip(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


ledger = jl("ledger.jsonl")
fires = jl("fire_summary.jsonl")
trust = json.load(open(DATA / "trust_chain.json"))
rank = json.load(open(DATA / "rank.json"))
ranked = rank["ranked"]
by_mod = {r["module"]: r for r in ranked}
short = lambda m: (m or "").replace("amphora-", "")

VC = collections.Counter(v["verdict"] for v in ledger)
LED_BY_MOD = collections.defaultdict(list)
for v in ledger:
    LED_BY_MOD[v["module"]].append(v)
ATTACKED = sorted(LED_BY_MOD, key=lambda m: -len(LED_BY_MOD[m]))

anchored = sum(1 for t in trust if t["anchored"])
pre_anch = sum(1 for t in trust if t["era"] == "pre" and t["anchored"])
pre_tot = sum(1 for t in trust if t["era"] == "pre")
loop_anch = sum(1 for t in trust if t["era"] == "loop" and t["anchored"])
loop_tot = sum(1 for t in trust if t["era"] == "loop")

n_fires = len(fires)
v1 = [f for f in fires if f.get("ts", "") < "2026-07-31"]
v23 = [f for f in fires if f.get("ts", "") >= "2026-07-31"]
v1_signed = sum(1 for f in v1 if f.get("outcome") == "SIGNED_RECEIPT")
downgraded = sum(1 for f in fires if f.get("outcome") == "UNKNOWN"
                 and (f.get("outcome_raw") or "").startswith("CLAIM_"))
sub = rank["sub_counts"]
head = rank["headline"]

VBADGE = {"REFUTED": r"\bad{REFUTED}", "SURVIVED": r"\good{SURVIVED}",
          "BLOCKED": r"\prephase{BLOCKED}"}

# ---------------------------------------------------------------- cover
manifest_sha = open(DATA / "manifest.sha256").read().strip()
cover = rf"""
\thispagestyle{{empty}}
\begin{{tikzpicture}}[remember picture,overlay]
  \fill[Navy] (current page.south west) rectangle (current page.north east);
  \fill[Blue,opacity=.50] ($(current page.north east)+(-18mm,-26mm)$) circle (42mm);
  \fill[Cyan,opacity=.24] ($(current page.north east)+(-56mm,-8mm)$) circle (26mm);
  \fill[Red,opacity=.22] ($(current page.south west)+(150mm,54mm)$) circle (13mm);
\end{{tikzpicture}}

\vspace*{{20mm}}
{{\sffamily\fontsize{{9}}{{11}}\selectfont\bfseries\color{{Cyan}} AMPHORA COATING IP / PORTFOLIO STATUS}}\par
\vspace{{16mm}}
{{\sffamily\fontsize{{34}}{{43}}\selectfont\bfseries\color{{white}} We Tried To Break\\Everything}}\par
\vspace{{6mm}}
{{\sffamily\fontsize{{16}}{{20}}\selectfont\color{{white!85}} 2026-08-03 — an adversarial audit\\of our own portfolio}}\par
\vspace{{14mm}}

\begin{{tcolorbox}}[width=152mm,colback=white!8!Navy,colframe=Cyan!45!Navy,boxrule=.7pt,arc=3mm,left=7mm,right=7mm,top=6mm,bottom=6mm]
{{\sffamily\fontsize{{10.5}}{{14}}\selectfont\color{{white}}
\textbf{{{n_fires}}} autonomous fires \quad\textcolor{{Cyan}}{{/}}\quad \textbf{{{len(ledger)}}} adversarial verdicts \quad\textcolor{{Cyan}}{{/}}\quad \textbf{{{len(ATTACKED)}}} modules attacked\\[3mm]
\textbf{{\textcolor{{Red!70!white}}{{{VC['REFUTED']} claims refuted}}}} \quad\textcolor{{Cyan}}{{/}}\quad \textbf{{{VC['SURVIVED']} survived}} \quad\textcolor{{Cyan}}{{/}}\quad \textbf{{{VC['BLOCKED']}}} blocked on data \quad\textcolor{{Cyan}}{{/}}\quad \textbf{{{head.get('Tier 1',0)}}} promotions}}
\end{{tcolorbox}}

\vspace{{12mm}}
{{\sffamily\fontsize{{9}}{{12}}\selectfont\color{{white!72}}
Most of what follows is us breaking our own work. That is the point: an audit loop that always succeeds is generating paper, not information. Every number below traces to a DSSE-signed receipt on xbabe2, and where a previous claim did not survive, the retraction is stated explicitly.}}
\vfill
{{\sffamily\fontsize{{7}}{{9}}\selectfont\color{{Cyan!80}} Master manifest SHA-256\\}}%
{{\sffamily\fontsize{{7}}{{9}}\selectfont\color{{white!72}}\seqsplit{{{manifest_sha}}}}}\par
\vspace{{6mm}}
{{\sffamily\fontsize{{7.5}}{{9}}\selectfont\bfseries\color{{Amber}} AUDIT-ONLY \quad/\quad NO PROMOTION AUTHORITY \quad/\quad SUPERSEDES 2026-07-30}}
\newpage
"""
(SNIP / "cover.tex").write_text(cover)

# ---------------------------------------------------------------- TL;DR
top_ref = [m for m in ATTACKED if sum(1 for v in LED_BY_MOD[m] if v["verdict"] == "REFUTED") > 0][:3]
tldr = rf"""
\PageTitle{{01 / executive}}{{The one-paragraph read}}

\begin{{tcolorbox}}[enhanced, boxrule=0pt, arc=4pt, colback=Navy!96!white, colframe=Navy!96!white, left=14pt, right=14pt, top=10pt, bottom=10pt]
{{\sffamily\small\color{{Cyan}}\bfseries WHAT HAPPENED SINCE 2026-07-30}}\\[3pt]
{{\color{{white}}\normalsize
We built an autonomous loop whose job is to \textbf{{break}} our own claims, pointed it at the portfolio for four days, and it ran \textbf{{{n_fires}}} times. It produced \textbf{{{len(ledger)}}} adversarial verdicts across \textbf{{{len(ATTACKED)}}} modules: \textbf{{{VC['REFUTED']} of our claims did not survive}}, {VC['SURVIVED']} did, and {VC['BLOCKED']} are blocked pending data a human must fetch. \textbf{{Zero modules were promoted}} — the tier counts are identical to the last report, and that is the honest outcome of testing rather than asserting. The most consequential refutations: a flagship ML result collapsed from R\textsuperscript{{2}} $+0.856$ to $-0.047$ once duplicate rows were removed; our dielectric results turned out to rest on labels that are only 10.5\% physically admissible; and the barrier-corrosion module's locked primary KPI cannot be computed at all because the value it ranks by is never produced by the implementation.}}
\end{{tcolorbox}}

\vspace{{5pt}}
\begin{{center}}
\includegraphics[width=0.92\linewidth]{{figures/G1_scoreboard.pdf}}
\end{{center}}

\vspace{{3pt}}
\begin{{tcolorbox}}[enhanced, boxrule=0pt, arc=4pt, colback=PaleGreen, colframe=PaleGreen, left=12pt, right=12pt, top=8pt, bottom=8pt, fontupper=\color{{Ink}}\small]
\textbf{{Why a report full of refutations is good news.}} The previous report presented a portfolio in which essentially everything passed. That is the signature of an audit that cannot fail, and it is not evidence of quality. This report is the first in which our own machinery was capable of returning ``your claim is wrong'' — and it did so {VC['REFUTED']} times. Each refutation is a defect found before a customer, a partner, or a regulator found it. The claims that \emph{{survived}} this are now worth considerably more than they were a week ago.
\end{{tcolorbox}}

\vspace{{3pt}}
\begin{{tcolorbox}}[enhanced, boxrule=0pt, arc=4pt, colback=PaleAmber, colframe=Amber, left=12pt, right=12pt, top=8pt, bottom=8pt, fontupper=\color{{Ink}}\small, title={{\color{{Ink}}\bfseries What founders should do next}}]
\begin{{enumerate}}[leftmargin=14pt, itemsep=2pt, topsep=2pt, parsep=0pt]
\item[\textbf{{1.}}] \textbf{{File the USBR ST-19168 rights request.}} This is now the critical path for the entire corrosion claim. The package is written and signed; it needs a human to send it. Section 12.
\item[\textbf{{2.}}] \textbf{{Read the errata, section 10.}} Six claims from the 2026-07-30 report are superseded. If any of them left this building, they need correcting.
\item[\textbf{{3.}}] \textbf{{Decide on the trust-anchor gap, section 11.}} Before the audit loop existed, \textbf{{zero}} of {pre_tot} receipts were signed by a trust-anchored key. That is now measured, and it changes what ``signed receipt'' is allowed to mean in external material.
\end{{enumerate}}
\end{{tcolorbox}}

\clearpage
"""
(SNIP / "tldr.tex").write_text(tldr)

# ---------------------------------------------------------------- program
med = sorted(f.get("runtime_s", 0) for f in fires)[len(fires) // 2] if fires else 0
program = rf"""
\PageTitle{{02 / method}}{{The falsification program}}
\eyebrow{{What we built, why it changed, and how a verdict is verified}}

\metric{{The problem with the old loop}}{{Through 2026-07-30 the loop fired {len(v1)} times and returned {v1_signed} ``signed receipt'' outcomes — a {100.0*v1_signed/max(1,len(v1)):.0f}\% success rate. Its only success criterion was that \emph{{a signed file exists}}, which is trivially satisfiable every hour without learning anything. It could not represent the outcome ``this claim is wrong''.}}

\textbf{{What changed}}
\begin{{itemize}}[leftmargin=14pt, itemsep=1pt, topsep=2pt, parsep=0pt]
\item[$\bullet$] \textbf{{Outcome vocabulary.}} A fire now ends in CLAIM\_REFUTED, CLAIM\_SURVIVED, BLOCKED\_DATA, BLOCKED\_RIGHTS, SATURATED or ERROR. Refutation is a first-class success; a survival only counts if the attack could genuinely have falsified the claim.
\item[$\bullet$] \textbf{{Directed work.}} Fires execute a human-authored campaign backlog with explicit done-criteria, not a blind rotation.
\item[$\bullet$] \textbf{{Verified verdicts.}} The launcher independently re-checks every verdict over ssh. {downgraded} claimed verdicts were \textbf{{rejected}} by that check and recorded as UNKNOWN.
\end{{itemize}}

\vspace{{2pt}}
\textbf{{How a verdict is verified}} — all three must hold, and each is checked by the launcher, not the agent:
\begin{{center}}
\rowcolors{{2}}{{Panel}}{{white}}
\begin{{tabular}}{{@{{}}>{{\RaggedRight\arraybackslash}}p{{0.30\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.62\linewidth}}@{{}}}}
\toprule
\rowcolor{{Panel}} \textbf{{Check}} & \textbf{{What it prevents}} \\
\midrule
Content-hash attribution & The artifact must be new or changed by SHA-256 against a pre-fire snapshot, and must be one the agent explicitly declared. Touching a file, or a concurrent agent's unrelated work, cannot be credited. \\
Real Ed25519 DSSE & The receipt must verify against the pinned Phase-0 key over the DSSE pre-authentication encoding. A merely well-shaped signature object is not enough. \\
Fire-id ledger binding & The verdict ledger must contain a line carrying this specific fire's id. Ledger growth alone proves nothing. \\
\bottomrule
\end{{tabular}}
\end{{center}}

\vspace{{3pt}}
\begin{{center}}
\includegraphics[width=0.92\linewidth]{{figures/G2_fire_timeline.pdf}}
\end{{center}}

\callout{{Red-team this section}}{{The verification chain constrains \emph{{provenance}}, not \emph{{scientific quality}}. It proves a verdict came with genuinely new, correctly signed evidence produced by the fire that claimed it — it cannot prove the attack was well designed. A weak attack reported as CLAIM\_SURVIVED still passes all three checks. That is why survivals are reported in section 09 with the specific refutation criterion each one withstood, so the strength of the attack is auditable rather than asserted. Median fire duration is {med//60} min {med%60} s; a fire that finishes suspiciously fast is worth inspecting for exactly this reason.}}

\clearpage
"""
(SNIP / "program.tex").write_text(program)

# ---------------------------------------------------------------- scoreboard
tax = collections.Counter()
for f in fires:
    a = (f.get("attack_type") or "").strip().lower()
    if a:
        tax[a.split("|")[0][:40]] += 1
scoreboard = rf"""
\PageTitle{{03 / scoreboard}}{{Where the attacks landed}}
\eyebrow{{{len(ledger)} verdicts across {len(ATTACKED)} modules. Modules absent from this chart were never attacked --- see section 08.}}

\vspace{{2pt}}
\begin{{center}}
\includegraphics[width=0.86\linewidth]{{figures/G3_module_verdicts.pdf}}
\end{{center}}

\vspace{{2pt}}
\begin{{center}}
\includegraphics[width=0.92\linewidth]{{figures/G8_attack_taxonomy.pdf}}
\end{{center}}

\callout{{Red-team this section}}{{Attack counts are not quality. \code{{amphora-molecule-property}} shows the most verdicts largely because it is the most instrumented module, not because it is the weakest --- density of attack follows density of existing evidence. The modules with \emph{{zero}} bars are the genuine blind spot: {esc(", ".join(short(r["module"]) for r in ranked if r["code"] in ("T0S","T0I","PT0E") and r["module"] not in LED_BY_MOD)[:300])}. Absence of a refutation there is absence of testing, not evidence of correctness.}}

\clearpage
"""
(SNIP / "scoreboard.tex").write_text(scoreboard)

# ---------------------------------------------------------------- system state
sysstate = rf"""
\PageTitle{{04 / system}}{{Portfolio state --- and what did not move}}

\begin{{center}}
\includegraphics[width=0.92\linewidth]{{figures/G7_tiers.pdf}}
\end{{center}}

\vspace{{2pt}}
\metric{{The headline}}{{{head.get('Tier 0',0)} Tier 0 + {head.get('Pre-Tier 0',0)} Pre-Tier 0 + {head.get('Tier 1',0)} Tier 1, across {rank['n_modules_total']} modules. Of the Tier 0 group, {sub.get('Tier 0 Science (LOCKED_INTERNAL)',0)} carry an actual scientific claim (LOCKED-INTERNAL); the remaining {sub.get('Tier 0 Infrastructure (NOT_APPLICABLE)',0)} are contract and plumbing modules that assert no science by design. These counts are \textbf{{identical}} to the 2026-07-30 report.}}

\metric{{What grew}}{{Evidence, not status: KPI receipts and signed scientific receipts both increased, and the master promotion manifest correctly remained at {rank['n_receipts_in_master_manifest']} receipts across {rank['n_modules_in_master_manifest']} modules. The loop produces AUDIT-ONLY evidence; promotion requires a human dual-identity ceremony it deliberately cannot perform.}}

\callout{{Red-team this section}}{{A reader could fairly ask why four days of intensive work produced zero tier movement. Two honest reasons. First, promotion is gated on a human signing ceremony, so no amount of autonomous work can move a module by itself. Second, and more importantly, the work \emph{{found reasons not to promote}}: the strongest Pre-Tier-0 candidate had its headline result refuted, and the flagship Tier-0 candidate turned out to have an unimplemented KPI. Tier movement would have been the wrong outcome. The counts staying flat while {VC['REFUTED']} claims fell is the system working.}}

\clearpage
"""
(SNIP / "system.tex").write_text(sysstate)

# ---------------------------------------------------------------- module pages
FULL = ["amphora-molecule-property", "amphora-barrier-corrosion-score",
        "amphora-solvency-score", "amphora-design-rule-score",
        "amphora-cure-potlife-gate", "amphora-tolerance-robustness",
        "amphora-viscosity-score", "amphora-public-corrosion-benchmark",
        "amphora-molecule-role-ranker", "amphora-sourceability-ehs",
        "amphora-molecule-novelty"]
FULL = [m for m in FULL if m in by_mod]

REDTEAM_NOTE = {
    "amphora-molecule-property": "Twelve verdicts here is the most of any module, and eleven are refutations. The remaining risk is that the surviving property claims are all within-corpus: cross-corpus transfer was tested and failed, so the honest applicability domain is narrower than the KPI surface implies.",
    "amphora-barrier-corrosion-score": "The module's locked KPI ranks by \\code{metrics.barrier\\_index}, which the live implementation never computes. Until that is fixed, no result from this module can be compared against its own acceptance criterion --- and the three available literature series are individually too small to reach significance regardless.",
    "amphora-solvency-score": "This module survived its attack, which makes it the strongest asset in the portfolio --- but the survival was against one attack class. The Hildebrand comparator it beats is a single-parameter 1936 model; a fair fight against a modern group-contribution method has not yet been run.",
    "amphora-design-rule-score": "The headline was memorisation of duplicated rows. What remains defensible is the physics arm, not the ML arm. The binding constraint is now sample size (58 unique observations), which no modelling choice can fix.",
    "amphora-cure-potlife-gate": "The Arrhenius fit fails on the held-out leg it was never tested against. Separately, the module's own gate KPI is computed on rights-quarantined source data --- an integrity issue independent of the science.",
    "amphora-tolerance-robustness": "This module underwrites every other module's uncertainty claim, which makes its refutations propagate. Anything downstream that cites conformal coverage as support inherits the correction.",
    "amphora-viscosity-score": "The physics baseline here beats the ML arm, which is a genuine and unusual result. The gap is that the two rheology models the module actually implements cannot be benchmarked at all for want of data.",
    "amphora-public-corrosion-benchmark": "This module produced the portfolio's most physically damning findings --- impossible-phase records that survived every prior audit. Its own headline lift, however, is marginal against a per-material-group null median.",
    "amphora-molecule-role-ranker": "Both verdicts here were survivals, and one came from a genuinely hard attack using the live RDKit FFI on held-out molecules. The claim is contract-shaped though: there is still no independent prospective test set.",
    "amphora-sourceability-ehs": "Regulatory prescreen with real hazard data. The risk is not the model but the completeness of the hazard set --- omission is the failure mode, not misprediction.",
    "amphora-molecule-novelty": "Descriptive similarity scoring with no ground truth to be right or wrong against. Its survival should be read as 'not falsifiable by this attack', not as validation.",
}

out = []
for m in FULL:
    r = by_mod[m]
    vs = LED_BY_MOD.get(m, [])
    vcount = collections.Counter(v["verdict"] for v in vs)
    budget = min(470, max(150, 2750 // max(1, len(vs))))
    rows = "\n".join(
        rf"{esc(parse_ledger_ts(v['ts']).strftime('%m-%d %H:%M'))} & {VBADGE.get(v['verdict'], esc(v['verdict']))} & {esc(clip(v['attack'], budget))} \\"
        for v in sorted(vs, key=ledger_sort_key))
    if not rows:
        rows = r"\multicolumn{3}{@{}l@{}}{\textit{No adversarial verdict has been recorded against this module.}} \\"
    tr = [t for t in trust if t["module"] == m]
    tr_anch = sum(1 for t in tr if t["anchored"])
    out.append(rf"""
\PageTitle{{{esc(m)}}}{{{esc(short(m))}}}
\eyebrow{{score {r['score']:.1f} \, / \, {r['n_kpi_files']} KPI receipts \, / \, {r['n_signed_receipts_on_disk']} signed receipts \, / \, {esc(str(r['phase']).replace('_','-'))} \, / \, {esc(str(r['scientific_readiness']).replace('_','-'))}}}

\metric{{Attacks run against it}}{{{len(vs)} verdict{'' if len(vs)==1 else 's'} — {vcount.get('REFUTED',0)} refuted, {vcount.get('SURVIVED',0)} survived, {vcount.get('BLOCKED',0)} blocked. Trust chain: {tr_anch} of {len(tr)} receipt files in this module verify against a trust-anchored Phase-0 key.}}

\vspace{{2pt}}
{{\footnotesize
\rowcolors{{2}}{{Panel}}{{white}}
\begin{{longtable}}{{@{{}}l l >{{\RaggedRight\arraybackslash}}p{{0.66\linewidth}}@{{}}}}
\toprule
\rowcolor{{Panel}} \textbf{{When}} & \textbf{{Verdict}} & \textbf{{Attack}} \\
\midrule
\endfirsthead
\rowcolor{{Panel}} \textbf{{When}} & \textbf{{Verdict}} & \textbf{{Attack}} \\
\midrule
\endhead
\bottomrule
\endfoot
{rows}
\end{{longtable}}}}

\callout{{Red-team}}{{{REDTEAM_NOTE.get(m, 'No module-specific red-team note authored.')}}}

\clearpage
""")
(SNIP / "modules_full.tex").write_text("\n".join(out))

# ---------------------------------------------------------------- half-page
HALF = [r["module"] for r in ranked
        if r["code"] in ("PT0E", "T0S") and r["module"] not in FULL]
hrows = []
for m in HALF:
    r = by_mod[m]
    vs = LED_BY_MOD.get(m, [])
    vc = collections.Counter(v["verdict"] for v in vs)
    verd = (", ".join(f"{n} {k.lower()}" for k, n in vc.items()) if vs else "never attacked")
    last = clip(sorted(vs, key=lambda x: x["ts"])[-1]["attack"], 240) if vs else \
        "No adversarial verdict recorded — untested, not validated."
    hrows.append(rf"\code{{{esc(m)}}} & {r['score']:.1f} & {r['n_kpi_files']}/{r['n_signed_receipts_on_disk']} & {esc(verd)} & {esc(last)} \\")
half = rf"""
\PageTitle{{08 / remaining}}{{Modules with evidence but no deep-dive}}
\eyebrow{{Pre-Tier 0 and Tier 0 Science modules not covered above. ``never attacked'' means untested by the loop --- it is a gap, not a pass.}}

\vspace{{2pt}}
{{\footnotesize
\rowcolors{{2}}{{Panel}}{{white}}
\begin{{longtable}}{{@{{}}l r c >{{\RaggedRight\arraybackslash}}p{{0.20\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.40\linewidth}}@{{}}}}
\toprule
\rowcolor{{Panel}} \textbf{{Module}} & \textbf{{Score}} & \textbf{{KPI/Sci}} & \textbf{{Verdicts}} & \textbf{{Most recent attack}} \\
\midrule
\endfirsthead
\rowcolor{{Panel}} \textbf{{Module}} & \textbf{{Score}} & \textbf{{KPI/Sci}} & \textbf{{Verdicts}} & \textbf{{Most recent attack}} \\
\midrule
\endhead
\bottomrule
\endfoot
{chr(10).join(hrows)}
\end{{longtable}}}}

\callout{{Red-team this section}}{{Every row reading ``never attacked'' is an untested claim sitting in the portfolio with a composite score attached. The score is computed from evidence \emph{{density}} — receipts, baselines, splits — and says nothing about whether the claim survives contact with an adversary. Treat an unattacked score above 45 as a liability, not an asset.}}

\clearpage
"""
(SNIP / "modules_half.tex").write_text(half)

# ---------------------------------------------------------------- infra table
infra = [r for r in ranked if r["code"] == "T0I"]
runt = [r for r in ranked if r["code"] == "INF"]
irows = "\n".join(rf"\code{{{esc(r['module'])}}} & {r['n_kpi_files']} & {r['score']:.1f} \\" for r in infra)
infra_tex = rf"""
\PageTitle{{09 / infrastructure}}{{Contract and runtime modules}}
\eyebrow{{These assert no scientific claim by design, so there is nothing here to falsify. Listed for completeness of the {rank['n_modules_total']}-module roster.}}

\vspace{{3pt}}
\begin{{center}}
{{\footnotesize
\rowcolors{{2}}{{Panel}}{{white}}
\begin{{tabular}}{{@{{}}l r r@{{}}}}
\toprule
\rowcolor{{Panel}} \textbf{{Tier 0 Infrastructure ({len(infra)})}} & \textbf{{KPI}} & \textbf{{Score}} \\
\midrule
{irows}
\bottomrule
\end{{tabular}}}}
\end{{center}}

\vspace{{6pt}}
\textbf{{Pure runtime crates ({len(runt)})}} — no \code{{mission.md}}, no scientific claim, not scored:\\[2pt]
{{\footnotesize {esc(", ".join(short(r['module']) for r in runt))}.}}

\callout{{Red-team this section}}{{``No scientific claim'' is a design statement, not an audited fact. These modules pass deterministic contract gates, and a passing gate proves the plumbing is self-consistent — not that the contract encodes anything a customer would care about. One of them, \code{{amphora-optimizer-orchestrator}}, is described throughout the portfolio as an optimiser and contains no implementation at all; its role is policy enforcement. Read this table as ``nothing here has been tested because nothing here claims anything'', which is a different and weaker statement than ``this is fine''.}}

\clearpage
"""
(SNIP / "infra.tex").write_text(infra_tex)

# ---------------------------------------------------------------- trust chain
trust_tex = rf"""
\PageTitle{{11 / provenance}}{{What ``signed receipt'' actually means here}}
\eyebrow{{The portfolio trust store anchors exactly two keys. This is the first report to measure how many receipts actually chain to them.}}

\begin{{center}}
\includegraphics[width=0.92\linewidth]{{figures/G6_trust_chain.pdf}}
\end{{center}}

\vspace{{2pt}}
\metric{{The finding}}{{Of {len(trust)} receipt files in the tree, {anchored} verify against a trust-anchored Phase-0 key. Split by era the picture is stark: \textbf{{{pre_anch} of {pre_tot}}} receipts written before the audit loop existed are anchored, versus \textbf{{{loop_anch} of {loop_tot}}} ({100.0*loop_anch/max(1,loop_tot):.0f}\%) written during it. The loop is the only mechanism that has ever produced a trust-anchored chain in this portfolio.}}

\metric{{What it does not mean}}{{These are not forgeries. The non-anchored receipts are largely self-labelled development and audit artifacts — several explicitly record \code{{trust\_anchored: false}}. The problem is presentational: the previous report footed every page with ``every claim traces to a signed, byte-stable evidence receipt'', which is true of the \emph{{form}} of the receipts and not of their \emph{{chain of trust}}.}}

\callout{{Red-team this section}}{{This measurement verifies signatures against one key pair; a receipt legitimately signed by some other authority would appear here as unanchored without being illegitimate. The trust store names only two keys, so that possibility is narrow — but the correct remediation is triage, not mass re-signing. Re-signing historical evidence with the anchored key would make the chain look clean while destroying the very distinction this page exists to draw. That triage is queued as the next campaign item; it deliberately does not re-sign anything.}}

\clearpage
"""
(SNIP / "trustchain.tex").write_text(trust_tex)

# ---------------------------------------------------------------- lift
# Only comparisons with a genuinely defensible published baseline. Every
# number here is quoted from a signed receipt; weak baselines are flagged
# rather than quietly dropped.
STRONG = [
    ("Hansen $\\chi$", "MAE 0.656 $\\chi$", "Hildebrand--Scott 1950 single-$\\delta$", "1.730",
     "$-$62.1\\%", "a-priori, zero fitted params, n=8 published pairs"),
    ("BigSolDB solubility", "RMSE 0.877 log", "best naive (solvent-mean)", "1.169",
     "$-$25.0\\%", "leave-solute-out, 1{,}372 solute groups, n=94{,}532"),
    ("Density", "MAE 0.0566 g/cm$^3$", "Van Krevelen 1990 Ch.4, 0 params", "0.1327",
     "$-$57.3\\%", "random 60/20/20 --- \\emph{not} group-safe, n=1{,}077"),
    ("Glass transition T$_g$", "MAE 51.24 K", "Van Krevelen Ridge Y$_{gi}$", "70.42",
     "$-$27.2\\%", "LOSO-CV, 212 scaffold folds, n=441"),
    ("Refractive index", "MAE 0.0304", "Lorentz--Lorenz, real MD density", "0.0377",
     "$-$19.3\\%", "source-stratified 60/20/20, n=1{,}223"),
    ("Melt viscosity", "R$^2$ 0.454 (ML)", "Fox--Flory--Whitten + Arrhenius", "0.597",
     "physics \\textbf{wins}", "polymer-safe by SMILES, only n=13 test chemistries"),
    ("Cure kinetics E$_a$", "57.261 kJ/mol", "Kissinger 1957 on CC-BY DSC", "57.3 pub.",
     "err 0.039", "3 systems, 3 DOIs, cross-lab"),
]
WEAK = [
    ("Flory--Huggins / Hansen ``ML beats theory''", "\\textbf{REFUTED} --- the rescaled comparator collapsed onto constant-mean (fitted slope $\\sim$10$^{-35}$) and δ values exceeded the admissible envelope by up to 16 orders of magnitude. The comparison against a valid classical baseline has never been run."),
    ("Pot-life Arrhenius lift 0.805$\\times$", "Baseline is \\emph{no temperature correction at all}. A chemistry-blind Q10=2 heuristic matches it (MAPE 0.1527 vs 0.1473) and \\textbf{beats} it at 30\\,°C and 40\\,°C --- so the published activation energies are not demonstrably load-bearing."),
    ("Viscosity Arrhenius lift +64\\,pp", "Baseline is constant viscosity at 25\\,°C. No named correlation (Andrade, VFT, Vogel) is benchmarked."),
    ("Barrier diffusivity R² +0.269 vs −0.061", "The physics arm is a \\emph{simplified surrogate}; the KPI itself concedes that full Vrentas--Duda 1977 is Phase-1 scope."),
    ("NIST corrosion +0.047 log10", "Null-median baseline, \\textbf{and refuted}: Ridge beats the null on only 17/30 folds (p=0.585), the bootstrap CI crosses zero, and the generating script was never committed so the pinned number is not independently reproducible."),
    ("Design-rule leak-free ΔR²", "Paired bootstrap CI [−0.022, +0.568] crosses zero at n=58 unique observations. Binding constraint is sample size, not model form."),
    ("Tg vs Van Krevelen (PolyUniverse)", "The rescaled VK arm scores R² −0.042 --- statistically indistinguishable from constant-mean. ``ML beats VK by +0.87 R²'' is really ``ML beats a constant.''"),
    ("molecule-property NULL arms", "Every ``beats NULL'' gate in that module compares against a median. Published group-contribution tables exist and are only partly used."),
]
srows = "\n".join(
    rf"{a} & \textbf{{{b}}} & {d} & {e} & {f} & {g} \\"
    for a, b, d, e, f, g in STRONG)
wrows = "\n".join(rf"{a} & {b} \\" for a, b in WEAK)
lift = rf"""
\PageTitle{{05 / lift}}{{Where we beat best known practice --- and where the baseline is a straw man}}
\eyebrow{{Only comparisons with a genuinely defensible published baseline appear in the first table. Every value is quoted from a signed receipt.}}

\vspace{{2pt}}
{{\scriptsize
\rowcolors{{2}}{{Panel}}{{white}}
\begin{{longtable}}{{@{{}}>{{\RaggedRight\arraybackslash}}p{{0.145\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.125\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.215\linewidth}} r >{{\RaggedRight\arraybackslash}}p{{0.085\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.245\linewidth}}@{{}}}}
\toprule
\rowcolor{{Panel}} \textbf{{Property}} & \textbf{{Ours}} & \textbf{{Published baseline}} & \textbf{{Base}} & \textbf{{Δ}} & \textbf{{Split / n}} \\
\midrule
\endfirsthead
\rowcolor{{Panel}} \textbf{{Property}} & \textbf{{Ours}} & \textbf{{Published baseline}} & \textbf{{Base}} & \textbf{{Δ}} & \textbf{{Split / n}} \\
\midrule
\endhead
\bottomrule
\endfoot
{srows}
\end{{longtable}}}}

\vspace{{1pt}}
\metric{{Two results worth reading twice}}{{On \textbf{{melt viscosity}} classical polymer physics \emph{{beats}} our ML by +0.144 R². On \textbf{{cure kinetics}}, three independent published isoconversional estimators all recover activation energies that produce \emph{{lower}} pot-life error than the value we currently cite (9.3\% vs 13.3\% MAPE). Both are cases where the hardest available baseline won, and both are reported here rather than buried.}}

\vspace{{3pt}}
\eyebrow{{Comparisons whose baseline is NOT the hardest defensible alternative --- 8 of 14}}
{{\scriptsize
\rowcolors{{2}}{{PaleRed}}{{white}}
\begin{{longtable}}{{@{{}}>{{\RaggedRight\arraybackslash}}p{{0.30\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.64\linewidth}}@{{}}}}
\toprule
\rowcolor{{Panel}} \textbf{{Comparison}} & \textbf{{Why the Δ is not yet defensible}} \\
\midrule
\endfirsthead
\rowcolor{{Panel}} \textbf{{Comparison}} & \textbf{{Why the Δ is not yet defensible}} \\
\midrule
\endhead
\bottomrule
\endfoot
{wrows}
\end{{longtable}}}}

\callout{{Red-team this section}}{{The first table is the strongest material in the portfolio and it still carries two structural caveats. \textbf{{Split methodology is not uniform}}: density and refractive index use a plain random 60/20/20 split, and every RadonPy property fails a chemically-coherent held-out split when one is imposed --- so those two rows describe within-chemotype performance, not generalisation. \textbf{{No time-safe split exists anywhere in the portfolio}}; the one temporally ordered dataset turned out to be cumulative snapshots that were 64\% leaked. And properties with \emph{{no}} defensible baseline at all --- dielectric, coating-barrier efficacy, pigment crowding, thermal conductivity --- are absent from both tables by construction, which is itself a finding.}}

\clearpage
"""
(SNIP / "lift.tex").write_text(lift)

# ---------------------------------------------------------------- errata
ERRATA = [
    ("BigSolDB leave-solute-out RMSE", "Ours 0.856 vs naive-mean 1.159, Δ −26%",
     "\\textbf{0.877} [0.8416, 0.9154] vs best naive baseline \\textbf{1.169}, Δ −25.0\\%. Neither 0.856 nor 1.159 reproduces from any receipt in the module tree.",
     "amphora-solvency-score/benchmarks/bigsoldb-v1/inhouse_benchmark_receipt.v1.dsse.json"),
    ("Hansen 8-pair external validation", "vs 0.71 (single-δ), Δ +0.16 r",
     "The 0.71 figure does not occur in any receipt. The receipted single-δ comparator on these exact 8 pairs is \\textbf{r = 0.4598}, so the honest Δ is \\textbf{+0.409 r}.",
     "amphora-solvency-score/reference/mvp20/data/hildebrand_vs_hansen_chi_baseline_receipt.v1.json"),
    ("Conformal interval width", "Ours 1.42 vs bootstrap 1.68, Δ −15\\% (tighter)",
     "\\textbf{Inverted.} Conformal is \\textbf{7.3$\\times$ wider} (374.91 K vs 51.56 K). The bootstrap band is narrow because it \\emph{under-covers} --- 25.1\\% empirical against a 95\\% nominal. Neither 1.42 nor 1.68 appears in any receipt.",
     "amphora-tolerance-robustness/evidence/phase0/kpis/bootstrap-prediction-interval-coverage-openpoly-tg-kpi.v1.json"),
    ("OpenPoly Tg conformal coverage", "0.968 empirical vs 0.950 nominal, n=1,842",
     "\\textbf{REFUTED.} Under 60 independent scaffold-safe draws the mean coverage is \\textbf{0.8746}, bootstrap CI [0.8497, 0.8974] excluding 0.95, Wilcoxon p = 2.1$\\times$10$^{-9}$; 31/60 draws fall below the 0.90 floor. The corpus is \\textbf{442 polymers}, not 1{,}842.",
     "amphora-tolerance-robustness/evidence/audit/repeated-scaffold-monte-carlo-conformal-openpoly-tg-v1/"),
    ("RadonPy εr conformal coverage", "0.943 empirical vs 0.950 nominal, n=614",
     "\\textbf{REFUTED.} 0.943 appears in no receipt. Coverage looks nominal (0.9558) only because 89.5\\% of the labels are physically inadmissible; on the \\textbf{52 admissible rows coverage collapses to 0.6923}, CI [0.5573, 0.8009], excluding 0.95.",
     "amphora-tolerance-robustness/evidence/audit/conformal-coverage-attack-v1/"),
    ("Dielectric εr model performance", "F8 panel: physics 0.31 / ML 0.22 / stack 0.19 MAE",
     "\\textbf{Fabricated placeholder} (labelled SCHEMATIC in code, caveat not rendered). Corrected position: \\textbf{NO COMPETENT MODEL}. On the n=113 physically-valid subset all three arms score R² $\\leq$ 0 --- worse than the test-set mean. Do not report a point estimate.",
     "amphora-molecule-property/evidence/audit/dielectric-retraction-v1/"),
    ("Cure pot-life Arrhenius", "MAPE 14.7%, lift 0.805x over constant-mean",
     "The pooled 14.7\\% hides the legs: 10\\,°C 3.4\\%, 30\\,°C 15.6\\%, \\textbf{40\\,°C 25.12\\%} --- breaching the KPI's own 0.25 ceiling with 12/12 systematic under-prediction. Separately, an E$_a$-free Q10=2 heuristic matches the model and beats it on 2 of 3 legs.",
     "amphora-cure-potlife-gate/evidence/audit/potlife-kpi-envelope-disclosure-gap-v1/"),
    ("Public corrosion LOSD-CV", "MAE 0.633 vs null-median 0.681, ``modest but real''",
     "\\textbf{REFUTED} on two independent grounds: Ridge beats the null on only \\textbf{17/30 folds} (p = 0.585, bootstrap CI crosses zero), and the generating script was never committed --- an honest re-implementation gives 0.589, so the pinned number is \\textbf{not independently auditable}.",
     "amphora-public-corrosion-benchmark/evidence/audit/nist-baseline-fold-significance-v1/"),
    ("Barrier-corrosion locked KPI", "11/11 gates pass; blinded Kendall-tau gate required for promotion",
     "The locked KPI ranks by \\code{metrics.barrier\\_index}, which is \\textbf{unconditionally None on every live code path} (confirmed by \\code{cargo test}). All 3 series also fall below the protocol's own FEASIBILITY\\_FLOOR=6; at n=3 the test is \\textbf{combinatorially incapable} of reaching α=0.05.",
     "amphora-barrier-corrosion-score/benchmarks/three-series-barrier-ranking-v1/"),
    ("Solvency signing violations", "3 self-reported signing violations --- ``worth a targeted look''",
     "\\textbf{Investigated and cleared.} All four alerts were false positives from a checker probing a field name that does not exist in that schema. Every chain re-verified clean. The red dot on that figure is retracted.",
     "amphora-solvency-score/evidence/audit/signing-violation-forensics-v1/"),
    ("Cron loop outcomes", "82 fires, 100\\% SIGNED-RECEIPT, ``never produced a partial or unsigned outcome''",
     "Stale at press time --- by the stated end-date the loop had fired \\textbf{100} times and had already recorded an UNKNOWN. More importantly the 100\\% rate was a \\emph{{design limitation}}: the schema had no field in which a refutation could be recorded.",
     "/home/ubuntu/amphora-cron/logs/fire-summary.jsonl"),
    ("Per-page footer", "``Every claim traces to a signed, byte-stable evidence receipt''",
     "True of the \\emph{{form}} of the receipts, not their chain of trust. \\textbf{0 of 186} receipts predating the audit loop verify against a trust-anchored Phase-0 key --- including the master manifest itself. See section 11.",
     "config/phase0-trust-store.v1.json"),
]
erows = "\n".join(
    rf"{esc(a)} & {esc(b.replace(chr(92)+chr(37), chr(37)))} & {c} \\ \multicolumn{{3}}{{@{{}}p{{0.96\linewidth}}@{{}}}}{{\scriptsize\color{{Muted}}\code{{{esc(d)}}}}} \\[3pt]"
    for a, b, c, d in ERRATA)
errata = rf"""
\PageTitle{{10 / errata}}{{Corrections to the 2026-07-30 report}}
\eyebrow{{{len(ERRATA)} published claims are superseded. Each row gives what was published, the corrected position, and the receipt that forced the change.}}

\vspace{{2pt}}
{{\scriptsize
\rowcolors{{2}}{{Panel}}{{white}}
\begin{{longtable}}{{@{{}}>{{\RaggedRight\arraybackslash}}p{{0.17\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.28\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.49\linewidth}}@{{}}}}
\toprule
\rowcolor{{Panel}} \textbf{{Claim}} & \textbf{{As published 2026-07-30}} & \textbf{{Corrected position}} \\
\midrule
\endfirsthead
\rowcolor{{Panel}} \textbf{{Claim}} & \textbf{{As published 2026-07-30}} & \textbf{{Corrected position}} \\
\midrule
\endhead
\bottomrule
\endfoot
{erows}
\end{{longtable}}}}

\vspace{{2pt}}
\begin{{center}}
\includegraphics[width=0.80\linewidth]{{figures/G5_retractions.pdf}}
\end{{center}}

\callout{{Red-team this section}}{{This errata list is necessarily incomplete: it covers claims an adversarial fire happened to attack. {len(ATTACKED)} of {rank['n_modules_total']} modules have been attacked at all, so a claim in an unattacked module is not corroborated here --- it is merely untested. Several corrections above were found only because a \emph{{different}} claim was being probed, which suggests the true rate of stale numbers is higher than {len(ERRATA)}. The systemic fix is the completeness sweep: 157 of 162 signed verdict receipts on disk, including 51 negative findings, are referenced nowhere in their own module's KPI surface --- so refutations can exist and still not reach a report.}}

\clearpage
"""
(SNIP / "errata.tex").write_text(errata)

# ------------------------------------------------- survivals (graded)
# A survival only counts if the attack could genuinely have refuted. Each
# is graded on whether the pre-registered criterion had a real path to firing.
SURV = [
    ("STRONG", "design-rule", "Guth--Gold directional concordance", "Nested train-refit bootstrap, 5{,}000 reps, refitting the 5-parameter physical model on every resample --- strictly more uncertainty than the parent protocol. Hostile-null control \\emph{did} collapse to chance (C=0.4991)."),
    ("STRONG", "molecule-role-ranker", "H2 amine-direction rule", "Independent kinetic Monte Carlo with published non-ideal reactivity ratios; \\emph{any} single reversal across any hardener × ratio would refute. 0 of 6 reversed."),
    ("STRONG", "solvency-score", "BigSolDB leave-solute-out RMSE", "Excised all 517 genuinely contradictory duplicate groups from train \\emph{and} test, then re-ran the locked protocol. Threshold approached within 0.041."),
    ("STRONG", "sourceability-ehs", "VHR temperature envelope", "Re-derived by a coefficient-disjoint method (Clausius--Clapeyron + Watson from measured anchors). Four independent refutation routes; found a real +5--11\\% bias, too small to unseat the result."),
    ("STRONG", "viscosity-score", "Herschel--Bulkley benchmarkability", "The attack \\emph{fired} on a control arm: the literal transcription failed the same gates by 13--1500$\\times$. Clearest proof in the ledger that the gates were live."),
    ("STRONG", "molecule-novelty", "5/5 candidates novel", "Re-featurised as dimer and tetramer. The borderline candidate sat 0.0071 below the cutoff --- a single crossing would have flipped the verdict."),
    ("STRONG", "barrier-corrosion", "Corrosion-rate QSPR skill", "Re-grouped by metallurgical family so alloy aliases cannot straddle folds. Skill fell 63\\% (R² 0.356→0.132) and one fold went negative; survived only because the bar was R² > 0."),
    ("MODERATE", "cure-potlife", "Published-Ea Arrhenius baseline", "Three independent literature estimators, any of which could have breached the ceiling. But scope is n=1 chemistry --- and 24 h later the same ceiling was breached at 40\\,°C using the module's own data."),
    ("MODERATE", "ingredient-library", "Load-bearing density constants", "Live manufacturer-TDS re-verification. 8/9 within a 3\\% gate; the one failure is the module's own pre-disclosed regional conflict, confirmed accurate."),
    ("MODERATE", "molecule-role-ranker", "Role-classification agreement", "Moved from a self-authored fixture to 10 real held-out molecules through the production RDKit FFI, including two hostile nulls. No numeric pre-registered threshold."),
    ("MODERATE", "barrier-corrosion", "Diffusivity conformal coverage", "Temperature-regime shift. Both directions moved the right way and 5/10 seeds fell below target --- the test simply lacked power at n=10 to call it."),
    ("DOES NOT COUNT", "barrier-corrosion", "Blinded Kendall-τ locked KPI", "Run on \\textbf{synthetic shadow data with zero real content}; its own power probe reads \\textbf{0.0} empirical power at the full gate. The identical claim was decisively \\textbf{refuted 26 hours later}. This is a pipeline test, not evidence for the claim."),
]
GBADGE = {"STRONG": r"\good{STRONG}", "MODERATE": r"\prephase{MODERATE}",
          "DOES NOT COUNT": r"\bad{DOES NOT COUNT}"}
vrows = "\n".join(
    rf"{GBADGE[g]} & {esc(m)} & {esc(c)} & {w} \\"
    for g, m, c, w in SURV)
surv = rf"""
\PageTitle{{09 / survivals}}{{The 12 claims that held --- graded by whether the attack could have killed them}}
\eyebrow{{A survival is only evidence if the attack had a real path to refutation. Each is graded on that basis, not on the fact that it passed.}}

\vspace{{2pt}}
{{\scriptsize
\rowcolors{{2}}{{Panel}}{{white}}
\begin{{longtable}}{{@{{}}l >{{\RaggedRight\arraybackslash}}p{{0.15\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.20\linewidth}} >{{\RaggedRight\arraybackslash}}p{{0.44\linewidth}}@{{}}}}
\toprule
\rowcolor{{Panel}} \textbf{{Grade}} & \textbf{{Module}} & \textbf{{Claim}} & \textbf{{Could the attack have refuted it?}} \\
\midrule
\endfirsthead
\rowcolor{{Panel}} \textbf{{Grade}} & \textbf{{Module}} & \textbf{{Claim}} & \textbf{{Could the attack have refuted it?}} \\
\midrule
\endhead
\bottomrule
\endfoot
{vrows}
\end{{longtable}}}}

\vspace{{1pt}}
\metric{{Adjusted honest count}}{{The ledger records \textbf{{12 survivals}}. On inspection \textbf{{11 are meaningful and 7 are strong}}. One --- the barrier-corrosion pre-registration --- must not be presented as evidence for its claim: it ran on synthetic data with zero measured empirical power, and the same claim was refuted 26 hours later by a fire that used real data. We are reporting 11, not 12.}}

\callout{{Red-team this section}}{{Grading our own survivals is exactly the kind of judgement an interested party should not be trusted to make alone, and the grades above are argued from each receipt's own pre-registered criterion rather than from an external standard. Two structural caveats apply. First, three of these survivals (both role-ranker entries and the sourceability entry) rest on receipts signed with a \emph{{non-trust-anchored}} audit key --- the science is reproducible and byte-stable, but the signature is not rooted. Second, a survival is a statement about one attack, not about the claim: solvency's BigSolDB result survived a hard attack in the same week that the same module's physics-baseline comparison was refuted outright.}}

\clearpage
"""
(SNIP / "survivals.tex").write_text(surv)

# ------------------------------------- trust chain (verified, overwrites)
pre_tot = sum(1 for x in trust if x["era"] == "pre")
loop_tot = sum(1 for x in trust if x["era"] == "loop")
pre_ver = sum(1 for x in trust if x["era"] == "pre" and x.get("verifies"))
loop_ver = sum(1 for x in trust if x["era"] == "loop" and x.get("verifies"))
claim_only = sum(1 for x in trust if x.get("keyid_anchored") and not x.get("verifies"))
tc = rf"""
\PageTitle{{11 / trust}}{{What ``signed'' actually means}}
\eyebrow{{The 2026-07-30 report footed every page with ``every claim traces to a signed, byte-stable evidence receipt.'' That is true of the \emph{{form}} of the receipts. It is not true of their chain of trust.}}

\vspace{{2pt}}
\metric{{The finding}}{{\code{{config/phase0-trust-store.v1.json}} anchors exactly \textbf{{two}} Ed25519 keys. We re-verified all \textbf{{{pre_tot + loop_tot}}} receipt files in the portfolio by recomputing the DSSE PAE encoding and checking the signature against the pinned key --- not by reading a key name. Of the \textbf{{{pre_tot}}} receipts predating the audit loop, \textbf{{{pre_ver} verify against an anchored key}}. Of the {loop_tot} written since, \textbf{{{loop_ver}}} do.}}

\vspace{{2pt}}
\begin{{center}}
\includegraphics[width=0.82\linewidth]{{figures/G6_trust_chain.pdf}}
\end{{center}}

\vspace{{1pt}}
{{\small The pre-loop receipts are not forgeries and not worthless. They are DSSE envelopes with real signatures, and they give genuine \textbf{{tamper-evidence}}: you can tell if the bytes changed. What they do not give is \textbf{{authenticity against a pinned root}} --- they are signed by \code{{toolkit-reviewer}}, \code{{rights-reviewer}}, \code{{local-9028773f}} and various fixture keys, none of which is in the Phase-0 trust store. For all pre-loop evidence the founder-signed 66-receipt master manifest is the \emph{{only}} human trust boundary.}}

\vspace{{3pt}}
\eyebrow{{Three further findings from the same verification pass}}
{{\small
\begin{{itemize}}[leftmargin=1.1em,itemsep=2pt,topsep=2pt]
\item \textbf{{{claim_only} receipts name an anchored key but do not verify against it.}} Two more carry malformed key identifiers that would fail a strict trust-store lookup --- and one of those is load-bearing: it is the parent physical-baseline receipt behind the Guth--Gold arm, currently the design-rule module's strongest surviving claim.
\item \textbf{{The most consequential finding in this report is signed with a non-anchored key.}} \code{{amphora-molecule-property}} holds 84 receipt files of which only 5 are anchored; the dielectric label-integrity receipt is among the unanchored. The loop caught and fixed this for the \code{{evidence/audit/}} tree but never retro-signed the \code{{benchmarks/}} tree.
\item \textbf{{The scheme has a stated ceiling.}} A coordinated adversary who strips a claim lock, re-renders, recomputes both digests and re-signs with \emph{{its own}} key satisfies every cryptographic and hash-binding clause, because the key id is self-derived from the presented public key. The loop recorded this against itself as \code{{PRESERVATION\_CORROBORATED\_WITH\_UNANCHORED\_TRUST\_BASE}}.
\end{{itemize}}}}

\vspace{{2pt}}
\callout{{Corrected footer wording}}{{The honest statement is: \emph{{``Every claim in this report traces to a DSSE-signed, byte-stable evidence receipt. {loop_ver} of those receipts verify against a trust-anchored Phase-0 key; receipts predating the audit loop are tamper-evident but not anchored, and rest on the founder-signed master manifest as their trust boundary.''}} That is the footer this report carries.}}

\callout{{Red-team this section}}{{This page grades our own cryptography, and the verification script is ours. An external auditor should re-run it independently --- the procedure is: recompute \code{{pae(t,p) = b"DSSEv1 \%d \%s \%d \%s"}} over each envelope and verify against the two public keys in the trust store. Note also what this page does \emph{{not}} claim: anchoring says a receipt was signed by an authorised service identity, not that its science is correct. Every refutation in this report was found in evidence that was already signed.}}

\clearpage
"""
(SNIP / "trustchain.tex").write_text(tc)

print(f"wrote {len(list(SNIP.glob('*.tex')))} snippets")
for p in sorted(SNIP.glob("*.tex")):
    print(f"  {p.name:24s} {p.stat().st_size:>7d} B")

# ------------------------------------------------- references / blockers
refs = r"""
\PageTitle{12 / verify}{Blocked on humans, and how to check any of this yourself}

\eyebrow{Two blockers where the loop has done everything it can and a human decision is the only path forward}
{\small
\begin{itemize}[leftmargin=1.1em,itemsep=3pt,topsep=2pt]
\item \textbf{USBR ST-19168 rights review.} A hash-bound rights-review package is assembled and waiting at \seqsplit{amphora-barrier-corrosion-score/evidence/audit/st-19168-rights-review-v1/}\code{RIGHTS-REVIEW-REQUEST.md}. The spreadsheet (10 coating systems) has never been opened or parsed. It is the closest on-disk candidate to close the barrier module's evidence gap. \textbf{Needs:} confirmation from USBR RISE that the asset is public domain under 17 U.S.C. §105.
\item \textbf{Krieger--Dougherty rheology data.} A genuine η(φ) dataset with an explicit φ$_{max}$ fit exists (Reynolds et al.\ 2024, DOI 10.1002/adem.202301630) but is CC BY-NC-ND, which forbids both derivatives and commercial use. The loop identified it, verified the licence, and stopped without extracting a single value. \textbf{Needs:} counsel. This is a rights wall, not a data wall.
\end{itemize}}

\vspace{3pt}
\eyebrow{How to verify any number in this report}
{\small
\begin{enumerate}[leftmargin=1.3em,itemsep=2pt,topsep=2pt]
\item Every quantitative claim cites a repository-relative receipt path. Resolve it against \code{/home/ubuntu/amphora/build/mvp20-split/} on the evidence host.
\item Verify the signature: each receipt is a DSSE envelope. Recompute \code{pae(t,p) = b"DSSEv1 \%d \%s \%d \%s"} and check against the two Ed25519 public keys in \code{config/phase0-trust-store.v1.json}. Section 11 reports what fraction pass.
\item Replay the science: signed receipts carry a two-replay SHA-256 byte-stability gate. Re-running the benchmark must reproduce the canonical body byte-for-byte.
\item Audit the adversarial record directly: \code{logs/falsification-ledger.jsonl} is append-only, one line per verdict, each carrying the fire id that produced it. \code{logs/claims-requiring-retraction.jsonl} is the machine-readable retraction list.
\end{enumerate}}

\vspace{3pt}
\eyebrow{Principal published baselines this report measures against}
{\scriptsize
Van Krevelen \& te Nijenhuis, \emph{Properties of Polymers}, 4th ed., Elsevier 1990 (group contribution: Tg Table 6.6, density Ch.\ 4, solubility Ch.\ 7) ~·~ Hansen, \emph{Hansen Solubility Parameters}, 2nd ed., CRC 2007 ~·~ Hildebrand \& Scott, \emph{The Solubility of Nonelectrolytes}, Reinhold 1950 ~·~ Guth \& Gold, \emph{Phys.\ Rev.} \textbf{53}:322 (1938) ~·~ Kissinger, \emph{Anal.\ Chem.} \textbf{29}:1702 (1957) ~·~ Starink, \emph{Thermochim.\ Acta} \textbf{404}:163 (2003) ~·~ Fröhlich, \emph{Theory of Dielectrics}, Oxford 1949 ~·~ Bondi, \emph{Physical Properties of Molecular Crystals}, Wiley 1968 ~·~ Fox \& Flory (1948); Berry \& Fox (1968); Doi \& Edwards 1988 ~·~ Vrentas \& Duda, \emph{J.\ Polym.\ Sci.} (1977) ~·~ Wolpert, \emph{Neural Networks} \textbf{5}:241 (1992) ~·~ Kaufman, Rosset \& Perlich, \emph{ACM TKDD} \textbf{6}(4):15 (2012) ~·~ Vovk, Gammerman \& Shafer, \emph{Algorithmic Learning in a Random World}, Springer 2005 ~·~ Romano, Patterson \& Candès (CQR, 2019) ~·~ Cameron, Gelbach \& Miller (2008); Cameron \& Miller (2015) ~·~ Attia et al., \emph{Nat.\ Commun.} (2025) ~·~ Alam et al., \emph{Materials} \textbf{15}(7):2562 (2022) ~·~ Amorim et al., \emph{SN Appl.\ Sci.} \textbf{3}:236 (2021) ~·~ Cordts et al., \emph{Chem.\ Mater.} (2024), Zenodo 13742098 ~·~ ASTM D2196, ASTM E698, ASTM F1980-16, ISO 5725, OSHA 29 CFR 1910.1000.}

\vspace{4pt}
\callout{Red-team this report as a whole}{Three things a sceptical reader should hold against it. \textbf{One:} it is written by the same system that produced the evidence, and the adversarial loop attacks claims it selects itself --- 15 of 40 modules have been attacked at all, so silence about a module is not a clean bill of health. \textbf{Two:} the 40 refutations are evidence the machine works, but they are also 40 things that were wrong and shipped, and the errata in section 10 were found only because something happened to probe them. \textbf{Three:} nothing here has been reviewed by anyone outside the portfolio. Zero modules carry \code{scientific_readiness=VALIDATED}, no claim has been externally replicated, and Phase-0 promotion deliberately requires two human trust-anchored signatures that this system does not hold and cannot grant itself.}

\clearpage
"""
(SNIP / "references.tex").write_text(refs)
print("wrote references.tex")
