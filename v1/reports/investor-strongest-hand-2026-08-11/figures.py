#!/usr/bin/env python3
"""Figures for the Amphora strongest-hand investor deck.

Every number is transcribed from the 2026-08-03 portfolio-status lift table
(signed-receipt-quoted, post-errata). Do not edit values without a receipt.
"""
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
import numpy as np

# ---- Amphora house palette (from reports/portfolio-status main.tex) ----
NAVY   = "#102A43"
BLUE   = "#1666A8"   # Amphora series
CYAN   = "#2D9CDB"
GREEN  = "#23856D"
DELTA_GREEN = "#006300"  # delta-good text token (light surface)
RED    = "#B54747"
AMBER  = "#D99A1D"
INK    = "#243B53"
MUTED  = "#627D98"
BASE   = "#7D8A96"   # de-emphasized published-baseline series (validated pair w/ BLUE)
LINE   = "#D9E2EC"
PANEL  = "#F4F7FA"

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],
    "text.color": INK,
    "axes.edgecolor": LINE,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
})

FIGDIR = "figs"


def rounded_top_bar(ax, x, height, width, color, radius_pt=2.6, zorder=3):
    """Bar with rounded data-end (top), square baseline, per mark spec."""
    # radius in data units, derived from axes size so it is ~4px on the page
    fig = ax.figure
    bbox = ax.get_window_extent(renderer=fig.canvas.get_renderer())
    ylim = ax.get_ylim()
    r_y = (ylim[1] - ylim[0]) * (radius_pt * fig.dpi / 72.0) / bbox.height
    r_x = width * 0.18
    r_y = min(r_y, height * 0.45)
    x0, x1 = x - width / 2, x + width / 2
    verts = [
        (x0, 0), (x0, height - r_y),
        (x0, height), (x0 + r_x, height),          # top-left corner curve
        (x1 - r_x, height),
        (x1, height), (x1, height - r_y),          # top-right corner curve
        (x1, 0), (x0, 0),
    ]
    codes = [Path.MOVETO, Path.LINETO,
             Path.CURVE3, Path.CURVE3,
             Path.LINETO,
             Path.CURVE3, Path.CURVE3,
             Path.LINETO, Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor=color,
                           edgecolor="none", zorder=zorder))


# ---------------------------------------------------------------- figure 1
# Small multiples: published baseline vs Amphora, one panel per property.
# (property, unit, baseline_label, baseline_val, ours_val, delta_label,
#  split/n footnote, value_fmt)
PANELS = [
    ("Hansen interaction parameter $\\chi$", "MAE ($\\chi$)",
     "Hildebrand–Scott\n1950 single-$\\delta$", 1.730, 0.656, "−62.1% error",
     "a-priori, zero fitted params · n=8 published pairs", "{:.3f}"),
    ("Polymer density", "MAE (g/cm$^3$)",
     "Van Krevelen 1990\ngroup contribution", 0.1327, 0.0566, "−57.3% error",
     "random 60/20/20 split · n=1,077 (within-chemotype)", "{:.4f}"),
    ("Glass transition $T_g$", "MAE (K)",
     "Van Krevelen\nRidge $Y_{gi}$", 70.42, 51.24, "−27.2% error",
     "LOSO-CV, 212 scaffold folds · n=441 · single-corpus", "{:.1f}"),
    ("Solubility (BigSolDB)", "RMSE (log $S$)",
     "Best naive\n(solvent-mean)", 1.169, 0.877, "−25.0% error",
     "leave-solute-out · 1,372 solutes · 94,532 groups", "{:.3f}"),
    ("Refractive index", "MAE ($n_D$)",
     "Lorentz–Lorenz,\nreal MD density", 0.0377, 0.0304, "−19.3% error",
     "source-stratified 60/20/20 · n=1,223", "{:.4f}"),
    ("Cure kinetics $E_a$ (parity)", "$E_a$ (kJ/mol)",
     "Kissinger 1957\non CC-BY DSC", 57.300, 57.261, "Δ 0.039 kJ/mol",
     "best of 3 labs · all 3 within 1.40 kJ/mol · 3 DOIs", "{:.2f}"),
]


def fig_main_lift():
    fig, axes = plt.subplots(2, 3, figsize=(12.4, 5.05))
    fig.subplots_adjust(left=0.033, right=0.985, top=0.80, bottom=0.125,
                        wspace=0.28, hspace=0.95)
    W = 0.34
    for ax, (title, unit, blab, bval, oval, dlab, foot, fmt) in zip(axes.flat, PANELS):
        parity = "parity" in title
        top = max(bval, oval)
        ax.set_xlim(-0.62, 1.62)
        ax.set_ylim(0, top * (1.45 if parity else 1.32))
        # draw AFTER limits so corner radius computes correctly
        rounded_top_bar(ax, 0, bval, W, BASE)
        rounded_top_bar(ax, 1, oval, W, BLUE)
        # value on the cap (text tokens, never series color)
        ax.text(0, bval + top * 0.045, fmt.format(bval), ha="center",
                va="bottom", fontsize=9.2, color=INK)
        ax.text(1, oval + top * 0.045, fmt.format(oval), ha="center",
                va="bottom", fontsize=9.2, color=INK, fontweight="bold")
        # delta badge (centered on parity panel so it clears the value label)
        ax.text(0.5 if parity else 1.0, top * (1.43 if parity else 1.24),
                dlab, ha="center", va="top", fontsize=9.4,
                color=(INK if parity else DELTA_GREEN), fontweight="bold")
        ax.set_xticks([0, 1])
        ax.set_xticklabels([blab, "Amphora"], fontsize=7.6, color=MUTED)
        ax.set_title(title, fontsize=10.6, color=NAVY, fontweight="bold", pad=26)
        ax.text(0.5, 1.115, unit, transform=ax.transAxes, ha="center",
                fontsize=7.6, color=MUTED)
        ax.set_yticks([])
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color("#C3CFD9")
        ax.text(0.5, -0.44, foot, transform=ax.transAxes, ha="center",
                fontsize=7.0, color=MUTED)
    # shared legend
    handles = [plt.Rectangle((0, 0), 1, 1, fc=BASE, ec="none"),
               plt.Rectangle((0, 0), 1, 1, fc=BLUE, ec="none")]
    fig.legend(handles, ["Published best practice (named method)",
                         "Amphora (signed receipt)"],
               loc="upper center", ncol=2, frameon=False, fontsize=9.6,
               bbox_to_anchor=(0.5, 1.0), handlelength=1.2,
               handleheight=1.05, columnspacing=1.8)
    fig.savefig(f"{FIGDIR}/lift_panels.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- flagship
def fig_flagship():
    """BigSolDB leave-solute-out RMSE vs best naive, with published SOTA band."""
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.90, bottom=0.135)
    ax.set_xlim(-0.75, 2.1)
    ax.set_ylim(0, 1.32)
    # published solute-extrapolation SOTA band (Attia et al. 2025): wash + hairlines
    ax.axhspan(0.83, 0.99, color=CYAN, alpha=0.10, zorder=1)
    for y in (0.83, 0.99):
        ax.axhline(y, color=CYAN, linewidth=0.8, alpha=0.55, zorder=1)
    ax.text(2.06, 1.045, "published solute-extrapolation\nSOTA band 0.83–0.99 (Attia et al. 2025)",
            ha="right", va="bottom", fontsize=7.6, color=MUTED, zorder=2)
    rounded_top_bar(ax, 0, 1.169, 0.34, BASE)
    rounded_top_bar(ax, 1, 0.877, 0.34, BLUE)
    # 95% CI whisker on the Amphora bar
    ax.plot([1, 1], [0.8416, 0.9154], color=INK, linewidth=1.1, zorder=4)
    ax.plot([0.955, 1.045], [0.8416, 0.8416], color=INK, linewidth=1.1, zorder=4)
    ax.plot([0.955, 1.045], [0.9154, 0.9154], color=INK, linewidth=1.1, zorder=4)
    ax.text(0, 1.169 + 0.05, "1.169", ha="center", va="bottom",
            fontsize=9.4, color=INK)
    ax.text(1, 0.44, "0.877", ha="center", va="center",
            fontsize=9.4, color="white", fontweight="bold")
    ax.text(0.5, 1.24, "−25.0% error", ha="center", va="top",
            fontsize=9.6, color=DELTA_GREEN, fontweight="bold")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Best naive\n(solvent-mean)", "Amphora\n(95% CI)"],
                       fontsize=8.0, color=MUTED)
    ax.set_yticks([0, 0.4, 0.8, 1.2])
    ax.tick_params(axis="y", labelsize=7.6, length=0)
    ax.grid(axis="y", color=LINE, linewidth=0.7)
    ax.set_axisbelow(True)
    ax.set_title("Solubility RMSE, log units — leave-solute-out (unseen solutes)",
                 fontsize=9.8, color=NAVY, fontweight="bold", pad=8, loc="left")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#C3CFD9")
    fig.savefig(f"{FIGDIR}/flagship_solubility.pdf")
    plt.close(fig)


# ---------------------------------------------------------------- figure 2
def fig_verdicts():
    """54 adversarial verdicts: refuted / survived / blocked, stacked."""
    fig, ax = plt.subplots(figsize=(7.6, 1.15))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.34)
    vals = [40, 12, 2]
    cols = [RED, GREEN, AMBER]
    labs = ["40 claims refuted", "12 survived", "2 blocked"]
    gap = 0.55
    x = 0.0
    for v, c, l in zip(vals, cols, labs):
        ax.barh(0, v, left=x, height=0.62, color=c, edgecolor="white",
                linewidth=1.6)
        if v >= 8:
            ax.text(x + v / 2, 0, l, ha="center", va="center", fontsize=10,
                    color="white", fontweight="bold")
        else:
            ax.text(x + v / 2, -0.62, l, ha="center", va="top", fontsize=8.6,
                    color=INK)
        x += v + 0 * gap
    ax.text(x + 0.6, 0, "", va="center")
    ax.set_xlim(0, 54.5)
    ax.set_ylim(-1.25, 0.55)
    ax.axis("off")
    fig.savefig(f"{FIGDIR}/verdicts.pdf")
    plt.close(fig)


if __name__ == "__main__":
    import os
    os.makedirs(FIGDIR, exist_ok=True)
    # a renderer must exist before get_window_extent
    mpl.use("Agg")
    fig_main_lift()
    fig_flagship()
    fig_verdicts()
    print("figures written")
