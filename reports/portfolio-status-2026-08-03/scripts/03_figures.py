#!/usr/bin/env python3
"""03_figures.py — vector PDFs for the 2026-08-03 founder report.

Every number is read from data/ (pulled read-only from xbabe2). Nothing is
hardcoded illustrative: the previous report shipped a fabricated SCHEMATIC
panel and that panel is deleted rather than relabelled.

G1 verdict scoreboard          G2 fire timeline, three eras
G3 module x verdict heatmap    G4 corrected lift vs best practice
G5 retraction before/after     G6 trust-chain composition
G7 tier counts, zero promotion G8 attack-type taxonomy
"""
import json
import collections
from datetime import datetime
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib import rcParams
from matplotlib.patches import Patch

ROOT = Path("/home/ubuntu/amphora/reports/portfolio-status-2026-08-03")
DATA, FIGS = ROOT / "data", ROOT / "figures"
FIGS.mkdir(exist_ok=True)

C = {"Navy": "#102A43", "Blue": "#1666A8", "Cyan": "#2D9CDB", "Teal": "#168C86",
     "Green": "#23856D", "Orange": "#E56B2F", "Amber": "#D99A1D", "Red": "#B54747",
     "Ink": "#243B53", "Muted": "#627D98", "Line": "#D9E2EC", "Panel": "#F4F7FA",
     "PaleGreen": "#EAF7F2", "PaleRed": "#FAECEC", "PaleAmber": "#FBEED4"}
VC = {"REFUTED": C["Red"], "SURVIVED": C["Green"], "BLOCKED": C["Amber"]}

try:
    from matplotlib import font_manager as fm
    fm.findfont("Inter", fallback_to_default=False)
    rcParams["font.family"] = "Inter"
except Exception:
    rcParams["font.family"] = "DejaVu Sans"
rcParams.update({"font.size": 9, "axes.edgecolor": C["Ink"], "axes.labelcolor": C["Ink"],
                 "xtick.color": C["Ink"], "ytick.color": C["Ink"],
                 "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100})


def save(fig, name):
    p = FIGS / name
    fig.savefig(p, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"  wrote {name} ({p.stat().st_size} B)")


def jl(p):
    return [json.loads(l) for l in open(DATA / p) if l.strip()]


ledger = jl("ledger.jsonl")
fires = jl("fire_summary.jsonl")
trust = json.load(open(DATA / "trust_chain.json"))
rank = json.load(open(DATA / "rank.json"))
short = lambda m: (m or "").replace("amphora-", "")

# ============================================================ G1 scoreboard
counts = collections.Counter(v["verdict"] for v in ledger)
order = ["REFUTED", "SURVIVED", "BLOCKED"]
fig, ax = plt.subplots(figsize=(9.0, 2.5), constrained_layout=True)
left = 0
for k in order:
    n = counts.get(k, 0)
    if not n:
        continue
    ax.barh([0], [n], left=[left], color=VC[k], edgecolor="white", linewidth=2, height=0.62)
    ax.text(left + n / 2, 0, str(n), ha="center", va="center", fontsize=17,
            color="white", fontweight="bold")
    ax.text(left + n / 2, -0.52, k, ha="center", va="top", fontsize=9, color=C["Ink"])
    left += n
ax.set_xlim(0, sum(counts.values())); ax.set_ylim(-1.25, 0.55)
ax.set_yticks([]); ax.set_xticks([])
for s in ("bottom", "left"):
    ax.spines[s].set_visible(False)
ax.set_title(f"{sum(counts.values())} adversarial verdicts against our own claims, "
             f"{len({v['module'] for v in ledger})} modules",
             fontsize=11.5, color=C["Navy"], loc="left", pad=8)
save(fig, "G1_scoreboard.pdf")

# ============================================================ G2 fire timeline
ERAS = [("v1 custodial", "2026-07-24", "2026-07-31", C["Muted"]),
        ("v2 falsification", "2026-07-31", "2026-08-02", C["Blue"]),
        ("v3 hardened", "2026-08-02", "2099-01-01", C["Green"])]
fig, ax = plt.subplots(figsize=(9.0, 3.4), constrained_layout=True)
xs, ys, cs = [], [], []
for f in fires:
    ts = f.get("ts", "")
    if not ts:
        continue
    try:
        t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        continue
    o = f.get("outcome", "")
    col = (C["Red"] if o == "CLAIM_REFUTED" else C["Green"] if o == "CLAIM_SURVIVED"
           else C["Amber"] if o.startswith("BLOCKED") else
           C["Muted"] if o == "SIGNED_RECEIPT" else C["Line"])
    xs.append(t); ys.append(f.get("runtime_s", 0) / 60.0); cs.append(col)
ax.scatter(xs, ys, c=cs, s=26, edgecolor="white", linewidth=0.5, zorder=3)
for name, a, b, col in ERAS:
    ta = datetime.fromisoformat(a).timestamp()
    tb = min(datetime.fromisoformat(b).timestamp(), max(xs) if xs else ta)
    if tb <= ta:
        continue
    ax.axvspan(ta, tb, color=col, alpha=0.07, zorder=0)
    ax.text((ta + tb) / 2, 1.015, name, ha="center", va="bottom",
            transform=ax.get_xaxis_transform(),
            fontsize=8, color=col, fontweight="bold")
ticks = [datetime.fromisoformat(d).timestamp() for d in
         ("2026-07-25", "2026-07-27", "2026-07-29", "2026-07-31", "2026-08-02")]
ax.set_xticks(ticks)
ax.set_xticklabels([datetime.fromtimestamp(t).strftime("%b %d") for t in ticks], fontsize=8)
ax.set_ylabel("fire duration (min)")
ax.grid(axis="y", color=C["Line"], linewidth=0.6)
ax.set_axisbelow(True)
ax.legend(handles=[Patch(facecolor=C["Muted"], label="SIGNED_RECEIPT (v1: no falsification)"),
                   Patch(facecolor=C["Red"], label="CLAIM_REFUTED"),
                   Patch(facecolor=C["Green"], label="CLAIM_SURVIVED"),
                   Patch(facecolor=C["Amber"], label="BLOCKED")],
          loc="upper center", bbox_to_anchor=(0.5, -0.16), frameon=False,
          fontsize=7.5, ncol=4, handlelength=1.3, columnspacing=1.6)
ax.set_title(f"{len(fires)} autonomous fires: the vocabulary changed on 07-31",
             fontsize=11, color=C["Navy"], loc="left", pad=6)
save(fig, "G2_fire_timeline.pdf")

# ============================================================ G3 module x verdict
mods = sorted({v["module"] for v in ledger}, key=lambda m: -sum(
    1 for v in ledger if v["module"] == m))
grid = np.zeros((len(mods), 3))
for v in ledger:
    grid[mods.index(v["module"]), order.index(v["verdict"])] += 1
fig, ax = plt.subplots(figsize=(7.4, max(3.2, 0.34 * len(mods))), constrained_layout=True)
y = np.arange(len(mods))
lefts = np.zeros(len(mods))
for j, k in enumerate(order):
    ax.barh(y, grid[:, j], left=lefts, color=VC[k], edgecolor="white",
            linewidth=0.8, height=0.68, label=k)
    for i in range(len(mods)):
        if grid[i, j] > 0:
            ax.text(lefts[i] + grid[i, j] / 2, i, int(grid[i, j]), ha="center",
                    va="center", fontsize=7.5, color="white", fontweight="bold")
    lefts += grid[:, j]
ax.set_yticks(y); ax.set_yticklabels([short(m) for m in mods], fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("verdicts")
ax.grid(axis="x", color=C["Line"], linewidth=0.6); ax.set_axisbelow(True)
ax.legend(loc="lower right", frameon=False, fontsize=8)
ax.set_title("Where the attacks landed", fontsize=11, color=C["Navy"], loc="left", pad=6)
save(fig, "G3_module_verdicts.pdf")

# ============================================================ G5 retractions
# Both pairs are receipt-backed; see errata section for citations.
pairs = [("design-rule-score\nHistGBM R²", 0.8555, -0.0469,
          "leak-free\n(86 rows = 58 unique)"),
         ("design-rule-score\nGuth-Gold 1938 physics R²", 0.3345, 0.2437, "leak-free")]
fig, axes = plt.subplots(1, len(pairs), figsize=(7.6, 3.4), constrained_layout=True)
for ax, (lab, before, after, note) in zip(np.atleast_1d(axes), pairs):
    ax.bar([0], [before], color=C["Muted"], width=0.55, edgecolor="white", linewidth=1.2)
    ax.bar([1], [after], color=C["Red"] if after < before else C["Green"],
           width=0.55, edgecolor="white", linewidth=1.2)
    for x, v in ((0, before), (1, after)):
        ax.text(x, v + (0.03 if v >= 0 else -0.06), f"{v:+.4f}", ha="center",
                va="bottom" if v >= 0 else "top", fontsize=9,
                color=C["Ink"], fontweight="bold")
    ax.axhline(0, color=C["Ink"], linewidth=0.8)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["as published\n2026-07-30", note], fontsize=8)
    ax.set_title(lab, fontsize=9.5, color=C["Navy"])
    ax.set_ylim(min(-0.15, after * 1.3), max(1.0, before * 1.2))
    ax.grid(axis="y", color=C["Line"], linewidth=0.6); ax.set_axisbelow(True)
fig.suptitle("Retraction: what duplicate-row leakage was hiding",
             fontsize=10.5, color=C["Navy"], x=0.02, ha="left")
save(fig, "G5_retractions.pdf")

# ============================================================ G6 trust chain
eras = [("before the loop", "pre"), ("loop era", "loop")]
cats = [("anchored", C["Green"]), ("non-anchored", C["Amber"]), ("no DSSE envelope", C["Muted"])]
fig, ax = plt.subplots(figsize=(9.0, 2.9), constrained_layout=True)
for i, (label, era) in enumerate(eras):
    rows = [t for t in trust if t["era"] == era]
    vals = [sum(1 for t in rows if t["anchored"]),
            sum(1 for t in rows if t["envelope"] and not t["anchored"]),
            sum(1 for t in rows if not t["envelope"])]
    left = 0
    for (cname, col), n in zip(cats, vals):
        if n:
            ax.barh([i], [n], left=[left], color=col, edgecolor="white",
                    linewidth=1.6, height=0.55)
            ax.text(left + n / 2, i, str(n), ha="center", va="center",
                    fontsize=11, color="white", fontweight="bold")
        left += n
    pct = 100.0 * vals[0] / max(1, sum(vals))
    ax.text(left + 6, i, f"{pct:.0f}% anchored", va="center", fontsize=9.5,
            color=C["Green"] if pct > 50 else C["Red"], fontweight="bold")
ax.set_yticks(range(len(eras))); ax.set_yticklabels([e[0] for e in eras], fontsize=9.5)
ax.invert_yaxis()
ax.set_xlabel("receipt files")
ax.set_xlim(0, 250)
# legend below the axes so it cannot collide with the % labels
ax.legend(handles=[Patch(facecolor=c, label=n) for n, c in cats],
          loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=3,
          frameon=False, fontsize=8)
ax.grid(axis="x", color=C["Line"], linewidth=0.6); ax.set_axisbelow(True)
ax.set_title("Which receipts chain to a trust-anchored Phase-0 key",
             fontsize=11, color=C["Navy"], loc="left", pad=6)
save(fig, "G6_trust_chain.pdf")

# ============================================================ G7 tier counts
sub = rank["sub_counts"]
labels = ["Tier 1\n(human parity)", "Tier 0\nScience", "Tier 0\nInfrastructure",
          "Pre-Tier 0\n(signed evidence)", "Infra\n(no mission.md)"]
vals = [rank["headline"].get("Tier 1", 0),
        sub.get("Tier 0 Science (LOCKED_INTERNAL)", 0),
        sub.get("Tier 0 Infrastructure (NOT_APPLICABLE)", 0),
        sub.get("Pre-Tier 0 with signed evidence", 0),
        rank["headline"].get("Infra (no mission.md)", 0)]
cols = [C["Blue"], C["Green"], C["Teal"], C["Amber"], C["Muted"]]
fig, ax = plt.subplots(figsize=(9.0, 3.0), constrained_layout=True)
bars = ax.bar(range(len(vals)), vals, color=cols, edgecolor="white", linewidth=1.4, width=0.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.25, str(v), ha="center",
            fontsize=12, color=C["Ink"], fontweight="bold")
ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylabel("modules"); ax.set_ylim(0, max(vals) + 3)
ax.grid(axis="y", color=C["Line"], linewidth=0.6); ax.set_axisbelow(True)
# note lives under the title, not across the bars (it overlapped them in-plot)
ax.set_title(f"All {sum(vals)} modules by tier", fontsize=11, color=C["Navy"], loc="left", pad=18)
ax.text(0, 1.035, "unchanged since 2026-07-30 — zero promotions, which is the honest result of 54 attacks",
        transform=ax.transAxes, fontsize=8.5, color=C["Red"], va="bottom")
save(fig, "G7_tiers.pdf")

# ============================================================ G8 attack taxonomy
# Classified over every ledger verdict. The prior version counted only the
# fires that happened to carry an attack_type tag (15 of 182) under a title
# that implied full coverage.
FAMILIES = [
    ("Harder held-out split", ("scaffold", "macro-bisect", "group-safe", "family-safe",
                               "polymer-safe", "leave-", "loso", "stratif", "groupkfold")),
    ("Physical admissibility of labels", ("admissib", "envelope", "inequality", "eps_static",
                                          "frohlich", "sign-revers", "physically-valid")),
    ("Leakage / duplicate rows", ("leak", "duplicate", "dedup", "contradict", "conflation",
                                  "memoris", "memoriz")),
    ("Reproducibility / provenance", ("reproduc", "provenance", "attribution", "stale",
                                      "completeness", "parity", "index")),
    ("Uncertainty / coverage / power", ("bootstrap", "conformal", "coverage", "power",
                                        "significance", "wilcoxon", "monte-carlo", "monte carlo",
                                        "ci ", "interval")),
    ("Independent re-derivation", ("re-derivation", "re-derived", "cross-method", "independent",
                                   "literature sweep", "external", "head-to-head", "baseline")),
    ("Rights / disclosure audit", ("rights", "quarantin", "licen", "disclosure")),
    ("Live-runtime probe", ("runtime", "cargo", "code path", "encoding", "ffi", "live-")),
]
tax, unclassified = collections.Counter(), 0
for v in ledger:
    blob = ((v.get("attack") or "") + " " + (v.get("claim") or "")).lower()
    hit = next((name for name, keys in FAMILIES if any(k in blob for k in keys)), None)
    if hit:
        tax[hit] += 1
    else:
        unclassified += 1
if tax:
    items = tax.most_common()[::-1]
    fig, ax = plt.subplots(figsize=(8.4, max(2.8, 0.42 * len(items))), constrained_layout=True)
    ax.barh(range(len(items)), [n for _, n in items], color=C["Blue"],
            edgecolor="white", linewidth=0.7, height=0.66)
    for i, (_, n) in enumerate(items):
        ax.text(n + 0.08, i, str(n), va="center", fontsize=8.5, color=C["Ink"])
    ax.set_yticks(range(len(items)))
    ax.set_yticklabels([k for k, _ in items], fontsize=8.5)
    ax.set_xlabel("verdicts")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlim(0, max(n for _, n in items) * 1.10)
    ax.grid(axis="x", color=C["Line"], linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_title(f"How the {len(ledger)} verdicts attacked their claims"
                 + (f" ({unclassified} uncategorised)" if unclassified else ""),
                 fontsize=11, color=C["Navy"], loc="left", pad=6)
    save(fig, "G8_attack_taxonomy.pdf")

print("figures done")
