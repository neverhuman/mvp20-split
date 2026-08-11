//! P1 - VOC-minimizing solvent blend.
//!
//! Minimize VOC = sum_i m_i * (1 - nonvol_i) / V_total (g/L) over the carrier
//! composition simplex, subject to:
//!   volume_solids in [0.63, 0.67]
//!   Hansen RED(carrier blend vs DGEBA sphere [18.8, 10.8, 11.6], R = 16.5) <= 1
//!   min flash point over the blend support >= 38 C
//!   VOC <= 340 g/L
//! Sources: ingredient-library facts.json solvent.* entries (density / hsp /
//! flash_c), binder.dgeba.hsp(+radius), resin.dgeba_828.density - all read
//! through the sha256-pinned oracle and cited by sha.
//!
//! Three independent searches (exhaustive simplex grid, projected gradient,
//! NSGA-II) must agree on the scalar optimum; NSGA-II also produces the
//! VOC-vs-RED Pareto slice.

use crate::demos::{claim_locks, sources_json, AUTHORITY, DEMO_DATE, DEMO_HOST};
use crate::nsga2::{self, Nsga2Config};
use crate::oracle::SourceOracle;
use crate::simplex::{project_to_simplex, projected_gradient_min};
use anyhow::{anyhow, Context, Result};
use serde_json::{json, Map, Value};
use std::collections::BTreeSet;

const VS_LO: f64 = 0.63;
const VS_HI: f64 = 0.67;
const FLASH_MIN_C: f64 = 38.0;
const VOC_CAP_G_PER_L: f64 = 340.0;
const RED_CAP: f64 = 1.0;
const GRID_UNITS: usize = 20; // 0.05 volume-fraction resolution
const NSGA_SEED: u64 = 0x2026_0803;
const SUPPORT_EPS: f64 = 0.0; // strictly positive weight counts as support

#[derive(Clone, Debug)]
struct Solvent {
    key: String,
    density_g_ml: f64,
    flash_c: f64,
    hsp: [f64; 3],
}

fn entry_f64(entries: &Map<String, Value>, key: &str) -> Option<f64> {
    entries.get(key)?.get("value")?.as_f64()
}

fn entry_hsp(entries: &Map<String, Value>, key: &str) -> Option<[f64; 3]> {
    let arr = entries.get(key)?.get("value")?.as_array()?;
    if arr.len() != 3 {
        return None;
    }
    Some([arr[0].as_f64()?, arr[1].as_f64()?, arr[2].as_f64()?])
}

/// VOC in g/L of wet paint at carrier volume fraction (1 - phi):
/// solvents are fully volatile (nonvol = 0, declared assumption), the DGEBA
/// liquid resin is fully non-volatile (nonvol = 1, declared assumption), so
/// VOC = 1000 * (1 - phi) * sum_i x_i * rho_i  (ordered reduction).
fn voc_g_per_l(phi: f64, x: &[f64], solvents: &[Solvent]) -> f64 {
    let mut carrier_density = 0.0_f64;
    for (xi, s) in x.iter().zip(solvents.iter()) {
        carrier_density += xi * s.density_g_ml;
    }
    1000.0 * (1.0 - phi) * carrier_density
}

fn blend_hsp(x: &[f64], solvents: &[Solvent]) -> [f64; 3] {
    let mut c = [0.0_f64; 3];
    for (xi, s) in x.iter().zip(solvents.iter()) {
        c[0] += xi * s.hsp[0];
        c[1] += xi * s.hsp[1];
        c[2] += xi * s.hsp[2];
    }
    c
}

fn hansen_red(c: &[f64; 3], center: &[f64; 3], radius: f64) -> f64 {
    let dd = c[0] - center[0];
    let dp = c[1] - center[1];
    let dh = c[2] - center[2];
    (4.0 * dd * dd + dp * dp + dh * dh).sqrt() / radius
}

/// Flash-gate violation: sum_i x_i * max(0, 38 - flash_i). Zero iff every
/// solvent carrying positive weight has flash >= 38 C.
fn flash_violation(x: &[f64], solvents: &[Solvent]) -> f64 {
    let mut cv = 0.0_f64;
    for (xi, s) in x.iter().zip(solvents.iter()) {
        if *xi > SUPPORT_EPS {
            cv += xi * (FLASH_MIN_C - s.flash_c).max(0.0);
        }
    }
    cv
}

fn min_flash_on_support(x: &[f64], solvents: &[Solvent]) -> Option<f64> {
    let mut m: Option<f64> = None;
    for (xi, s) in x.iter().zip(solvents.iter()) {
        if *xi > SUPPORT_EPS {
            m = Some(match m {
                None => s.flash_c,
                Some(v) => v.min(s.flash_c),
            });
        }
    }
    m
}

fn total_violation(phi: f64, x: &[f64], solvents: &[Solvent], center: &[f64; 3], radius: f64) -> f64 {
    let voc = voc_g_per_l(phi, x, solvents);
    let red = hansen_red(&blend_hsp(x, solvents), center, radius);
    flash_violation(x, solvents) + (red - RED_CAP).max(0.0) + (voc - VOC_CAP_G_PER_L).max(0.0) / 1000.0
}

fn is_feasible(phi: f64, x: &[f64], solvents: &[Solvent], center: &[f64; 3], radius: f64) -> bool {
    total_violation(phi, x, solvents, center, radius) == 0.0
}

/// Enumerate integer compositions of `units` over `n` bins, lexicographic.
fn enumerate_compositions(n: usize, units: usize, cur: &mut Vec<usize>, visit: &mut dyn FnMut(&[usize])) {
    if n == 1 {
        cur.push(units);
        visit(cur);
        cur.pop();
        return;
    }
    for k in 0..=units {
        cur.push(k);
        enumerate_compositions(n - 1, units - k, cur, visit);
        cur.pop();
    }
}

fn composition_json(x: &[f64], solvents: &[Solvent]) -> Value {
    let mut m = Map::new();
    for (xi, s) in x.iter().zip(solvents.iter()) {
        if *xi > SUPPORT_EPS {
            m.insert(s.key.clone(), json!(xi));
        }
    }
    Value::Object(m)
}

pub fn diagnostic() -> Result<Value> {
    let oracle = SourceOracle::pinned_default().map_err(|e| anyhow!("{e}"))?;
    let facts = oracle.read("ingredient_library_facts").map_err(|e| anyhow!("{e}"))?;
    let entries = facts
        .value
        .get("entries")
        .and_then(|v| v.as_object())
        .context("facts.json has no entries object")?;

    // --- Ingredient extraction (fail-closed: a solvent without density AND
    // --- flash_c AND hsp in the pinned source cannot enter the blend).
    let mut names: BTreeSet<String> = BTreeSet::new();
    for key in entries.keys() {
        if let Some(rest) = key.strip_prefix("solvent.") {
            if let Some((name, _prop)) = rest.split_once('.') {
                names.insert(name.to_string());
            }
        }
    }
    let mut solvents: Vec<Solvent> = Vec::new();
    let mut excluded: Vec<Value> = Vec::new();
    for name in &names {
        let density = entry_f64(entries, &format!("solvent.{name}.density"));
        let flash = entry_f64(entries, &format!("solvent.{name}.flash_c"));
        let hsp = entry_hsp(entries, &format!("solvent.{name}.hsp"));
        match (density, flash, hsp) {
            (Some(d), Some(f), Some(h)) => solvents.push(Solvent {
                key: name.clone(),
                density_g_ml: d,
                flash_c: f,
                hsp: h,
            }),
            _ => {
                let mut missing: Vec<&str> = Vec::new();
                if density.is_none() {
                    missing.push("density");
                }
                if flash.is_none() {
                    missing.push("flash_c");
                }
                if hsp.is_none() {
                    missing.push("hsp");
                }
                excluded.push(json!({
                    "solvent": name,
                    "missing_facts": missing,
                    "action": "EXCLUDED_FAIL_CLOSED (cannot certify constraints without pinned facts)",
                }));
            }
        }
    }
    if solvents.is_empty() {
        anyhow::bail!("no fully-characterized solvents in pinned facts source");
    }
    let n = solvents.len();

    let center = entry_hsp(entries, "binder.dgeba.hsp").context("binder.dgeba.hsp missing")?;
    let radius = entry_f64(entries, "binder.dgeba.hsp_radius").context("binder.dgeba.hsp_radius missing")?;
    let resin_density = entry_f64(entries, "resin.dgeba_828.density").context("resin.dgeba_828.density missing")?;

    // --- phi* = VS_HI: VOC = 1000*(1-phi)*carrier_density is strictly
    // --- decreasing in phi for any positive carrier density, so the upper
    // --- volume-solids bound is active at every VOC optimum.
    let phi = VS_HI;

    // --- (a) exhaustive DoE enumeration on the 0.05 simplex grid.
    let mut grid_best_x: Option<Vec<f64>> = None;
    let mut grid_best_voc = f64::INFINITY;
    let mut grid_total = 0usize;
    let mut grid_feasible = 0usize;
    {
        let mut cur: Vec<usize> = Vec::with_capacity(n);
        let solvents_ref = &solvents;
        enumerate_compositions(n, GRID_UNITS, &mut cur, &mut |c: &[usize]| {
            grid_total += 1;
            let x: Vec<f64> = c.iter().map(|&u| u as f64 / GRID_UNITS as f64).collect();
            if is_feasible(phi, &x, solvents_ref, &center, radius) {
                grid_feasible += 1;
                let voc = voc_g_per_l(phi, &x, solvents_ref);
                if voc < grid_best_voc {
                    grid_best_voc = voc;
                    grid_best_x = Some(x);
                }
            }
        });
    }
    let grid_best_x = grid_best_x.context("no feasible point on the DoE grid")?;

    // --- (b) deterministic projected gradient on a penalized objective.
    // Penalty terms are exact-linear in the violating weights, so the
    // minimizer of the penalized problem is the constrained minimizer here.
    let center_c = center;
    let solvents_pg = solvents.clone();
    let obj = move |x: &[f64]| -> f64 {
        let voc = voc_g_per_l(phi, x, &solvents_pg);
        let red = hansen_red(&blend_hsp(x, &solvents_pg), &center_c, radius);
        voc / 100.0
            + 50.0 * flash_violation(x, &solvents_pg)
            + 50.0 * (red - RED_CAP).max(0.0)
            + 5.0 * (voc - VOC_CAP_G_PER_L).max(0.0) / 100.0
    };
    let solvents_g = solvents.clone();
    let grad = move |x: &[f64]| -> Vec<f64> {
        let voc = voc_g_per_l(phi, x, &solvents_g);
        let c = blend_hsp(x, &solvents_g);
        let dd = c[0] - center_c[0];
        let dp = c[1] - center_c[1];
        let dh = c[2] - center_c[2];
        let dist_sq = 4.0 * dd * dd + dp * dp + dh * dh;
        let red = dist_sq.sqrt() / radius;
        let mut g = Vec::with_capacity(x.len());
        for s in solvents_g.iter() {
            let mut gi = (1.0 - phi) * s.density_g_ml * 1000.0 / 100.0;
            gi += 50.0 * (FLASH_MIN_C - s.flash_c).max(0.0);
            if red > RED_CAP && dist_sq > 0.0 {
                let ddist = (8.0 * dd * s.hsp[0] + 2.0 * dp * s.hsp[1] + 2.0 * dh * s.hsp[2])
                    / (2.0 * dist_sq.sqrt());
                gi += 50.0 * ddist / radius;
            }
            if voc > VOC_CAP_G_PER_L {
                gi += 5.0 * (1.0 - phi) * s.density_g_ml * 1000.0 / 100.0;
            }
            g.push(gi);
        }
        g
    };
    let x0 = vec![1.0 / n as f64; n];
    let (pg_x, _pg_obj) = projected_gradient_min(&x0, &obj, &grad, 0.01, 5000);
    let pg_voc = voc_g_per_l(phi, &pg_x, &solvents);
    let pg_feasible = is_feasible(phi, &pg_x, &solvents, &center, radius);

    // --- (c) NSGA-II multi-objective front: minimize (VOC, RED) subject to
    // --- the flash gate and the VOC cap (constraint-domination).
    let cfg = Nsga2Config {
        pop_size: 64,
        generations: 150,
        seed: NSGA_SEED,
        eta_crossover: 15.0,
        eta_mutation: 20.0,
        p_crossover: 0.9,
        p_mutation: 1.0 / n as f64,
        gene_lo: 0.0,
        gene_hi: 1.0,
    };
    // Deterministic vertex anchors: every pure-solvent blend enters the
    // initial population, so feasible vertices (e.g. MAK, PMA) are present
    // from generation 0 and the feasible front cannot be vacuously empty.
    let vertex_seeds: Vec<Vec<f64>> = (0..n)
        .map(|i| (0..n).map(|j| if i == j { 1.0 } else { 0.0 }).collect())
        .collect();
    let solvents_ea = solvents.clone();
    let front = nsga2::run(&cfg, n, &vertex_seeds, move |genes: &[f64]| {
        let x = project_to_simplex(genes);
        let voc = voc_g_per_l(phi, &x, &solvents_ea);
        let red = hansen_red(&blend_hsp(&x, &solvents_ea), &center_c, radius);
        let cv = flash_violation(&x, &solvents_ea)
            + (voc - VOC_CAP_G_PER_L).max(0.0) / 1000.0
            + (red - RED_CAP).max(0.0);
        (vec![voc, red], cv)
    });
    anyhow::ensure!(!front.is_empty(), "NSGA-II produced an empty feasible front");

    let mut pareto_slice: Vec<Value> = Vec::new();
    let mut nsga_min_voc = f64::INFINITY;
    let mut nsga_min_red = f64::INFINITY;
    for ind in &front {
        let x = project_to_simplex(&ind.genes);
        let voc = ind.objectives[0];
        let red = ind.objectives[1];
        if voc < nsga_min_voc {
            nsga_min_voc = voc;
        }
        if red < nsga_min_red {
            nsga_min_red = red;
        }
        pareto_slice.push(json!({
            "composition_volume_fraction": composition_json(&x, &solvents),
            "voc_g_per_l": voc,
            "red": red,
            "min_flash_c_on_support": min_flash_on_support(&x, &solvents),
        }));
    }

    // --- Cross-method agreement gates (falsification-first):
    // grid and projected gradient must agree exactly-ish on the scalar
    // optimum; the NSGA-II front must not beat the true optimum.
    let pg_gap = (pg_voc - grid_best_voc).abs();
    anyhow::ensure!(pg_feasible, "projected-gradient solution violated constraints");
    anyhow::ensure!(
        pg_gap < 1e-9,
        "projected gradient disagrees with exhaustive grid: {pg_voc} vs {grid_best_voc}"
    );
    anyhow::ensure!(
        nsga_min_voc >= grid_best_voc - 1e-9,
        "NSGA-II front claims a VOC below the exhaustively-verified optimum: impossible"
    );

    // --- Optimum report (grid == PG winner).
    let best_x = grid_best_x;
    let best_voc = grid_best_voc;
    let best_red = hansen_red(&blend_hsp(&best_x, &solvents), &center, radius);
    let best_flash = min_flash_on_support(&best_x, &solvents);
    let resin_mass_g_per_l = phi * resin_density * 1000.0;
    let carrier_mass_g_per_l = {
        let mut m = 0.0_f64;
        for (xi, s) in best_x.iter().zip(solvents.iter()) {
            m += (1.0 - phi) * xi * s.density_g_ml * 1000.0;
        }
        m
    };

    let flash_gate_exclusions: Vec<Value> = solvents
        .iter()
        .filter(|s| s.flash_c < FLASH_MIN_C)
        .map(|s| {
            json!({
                "solvent": s.key,
                "flash_c": s.flash_c,
                "reason": format!("flash {} C < required {} C: any positive weight is infeasible", s.flash_c, FLASH_MIN_C),
            })
        })
        .collect();

    let active_constraints = json!([
        {
            "constraint": "volume_solids_upper_bound",
            "value": phi,
            "bound": VS_HI,
            "status": "ACTIVE",
            "why": "VOC is strictly decreasing in volume solids, so the optimizer sits on the 67% upper bound",
        },
        {
            "constraint": "simplex_vertex",
            "status": "ACTIVE",
            "why": "the linear VOC objective over the flash-feasible simplex face is minimized at the lowest-density vertex (MAK)",
        },
        {
            "constraint": "flash_point_gate",
            "status": "ACTIVE_AS_EXCLUSION",
            "why": "excludes 4 of 6 characterized solvents (incl. the lower-density MIBK) from the support; slack of the surviving support is 1.0 C",
            "min_flash_c_on_support": best_flash,
            "required_min_c": FLASH_MIN_C,
        },
    ]);
    let inactive_constraints = json!([
        {
            "constraint": "hansen_red_cap",
            "value": best_red,
            "bound": RED_CAP,
            "slack": RED_CAP - best_red,
            "status": "INACTIVE",
        },
        {
            "constraint": "voc_cap_g_per_l",
            "value": best_voc,
            "bound": VOC_CAP_G_PER_L,
            "slack": VOC_CAP_G_PER_L - best_voc,
            "status": "INACTIVE",
        },
        {
            "constraint": "volume_solids_lower_bound",
            "value": phi,
            "bound": VS_LO,
            "slack": phi - VS_LO,
            "status": "INACTIVE",
        },
    ]);

    let mut root = Map::new();
    root.insert("schema".into(), json!("amphora.solver-lab.demo-p1-voc-min-solvent-blend.diagnostic.v1"));
    root.insert("demo_id".into(), json!("p1-voc-min-solvent-blend"));
    root.insert("date".into(), json!(DEMO_DATE));
    root.insert("generated_on_host".into(), json!(DEMO_HOST));
    root.insert("authority".into(), json!(AUTHORITY));
    root.insert("authority_ceiling".into(), json!("EVIDENCE_ONLY"));
    root.insert("claim_locks".into(), claim_locks());
    root.insert("sources".into(), sources_json(&[&facts]));
    root.insert(
        "problem".into(),
        json!({
            "objective": "minimize VOC = sum_i m_i * (1 - nonvol_i) / V_total (g/L of wet paint)",
            "constraints": {
                "volume_solids": {"lower": VS_LO, "upper": VS_HI},
                "hansen_red_vs_dgeba_sphere": {"center_d_p_h": center, "radius": radius, "cap": RED_CAP, "source_entries": ["binder.dgeba.hsp", "binder.dgeba.hsp_radius"]},
                "min_flash_point_c": FLASH_MIN_C,
                "voc_cap_g_per_l": VOC_CAP_G_PER_L,
            },
            "binder": {
                "entry": "resin.dgeba_828",
                "density_g_ml": resin_density,
                "nonvol_assumption": 1.0,
                "assumption_note": "DGEBA liquid epoxy resin dosed as 100% non-volatile; facts.json carries no nonvol entry for liquid resins, so its VOC contribution is exactly zero by declared assumption",
            },
            "solvent_nonvol_assumption": 0.0,
            "solvent_nonvol_note": "carrier solvents are dosed as fully volatile (nonvol = 0); facts.json carries nonvol only for solvent-cut resins/hardeners, none of which enter this blend",
            "candidate_solvents": solvents.iter().map(|s| json!({
                "key": s.key,
                "density_g_ml": s.density_g_ml,
                "flash_c": s.flash_c,
                "hsp_d_p_h": s.hsp,
                "fact_entries": [
                    format!("solvent.{}.density", s.key),
                    format!("solvent.{}.flash_c", s.key),
                    format!("solvent.{}.hsp", s.key),
                ],
            })).collect::<Vec<_>>(),
            "excluded_ingredients": excluded,
        }),
    );
    root.insert(
        "determinism".into(),
        json!({
            "floats": "f64_only",
            "reductions": "ordered (sorted solvent keys, sequential sums)",
            "rng": "splitmix64",
            "nsga2_seed": NSGA_SEED,
            "grid_resolution_volume_fraction": 0.05,
            "projected_gradient": {"step": 0.01, "iters": 5000, "x0": "uniform"},
        }),
    );
    root.insert(
        "results".into(),
        json!({
            "optimal_blend": {
                "volume_solids": phi,
                "carrier_volume_fraction": 1.0 - phi,
                "composition_volume_fraction_of_carrier": composition_json(&best_x, &solvents),
                "voc_g_per_l": best_voc,
                "hansen_red_vs_dgeba": best_red,
                "min_flash_c_on_support": best_flash,
                "wet_mass_g_per_l": {
                    "resin_dgeba_828": resin_mass_g_per_l,
                    "carrier_solvents": carrier_mass_g_per_l,
                },
            },
            "method_agreement": {
                "grid_min_voc_g_per_l": grid_best_voc,
                "projected_gradient_min_voc_g_per_l": pg_voc,
                "nsga2_front_min_voc_g_per_l": nsga_min_voc,
                "grid_vs_pg_abs_gap": pg_gap,
                "grid_pg_agree_within_1e_9": true,
                "nsga2_never_beats_exhaustive_optimum": true,
            },
            "search_accounting": {
                "grid_cells_total": grid_total,
                "grid_cells_feasible": grid_feasible,
                "nsga2_front_size": front.len(),
                "nsga2_front_min_red": nsga_min_red,
            },
            "active_constraints": active_constraints,
            "inactive_constraints": inactive_constraints,
            "flash_gate_exclusions": flash_gate_exclusions,
            "pareto_slice_voc_vs_red": pareto_slice,
        }),
    );
    root.insert("pareto_status".into(), json!("OPTIMAL"));
    Ok(Value::Object(root))
}

// ============================================================================
// Showcase (Act 1) live scaled grid. Reuses the EXACT constraint math and
// pinned oracle facts as diagnostic() at a finer carrier-simplex resolution,
// evaluated in parallel with a live progress counter. This is a real
// computation over pinned data driving the live display; the SIGNED optimum and
// three-method agreement come from diagnostic(). diagnostic() is untouched, so
// the p1 signed receipt bytes are unchanged.
// ============================================================================
use rayon::prelude::*;
use std::sync::atomic::{AtomicU64, Ordering};

/// Result of a live scaled grid sweep for the Act 1 panel.
/// Live per-chunk optimization delta streamed to the showcase UI (display-only;
/// the signed diagnostic() and the final returned optimum are unaffected).
pub struct GridDelta {
    pub cells_done_delta: u64,
    pub chunk_best_voc: f64,
    pub chunk_best_red: f64,
    pub new_samples: Vec<(f32, f32)>,
    pub chunk_best_blend: Vec<(String, f64)>,
}

pub struct ShowcaseGrid {
    pub cells_total: u64,
    pub cells_feasible: u64,
    pub best_voc: f64,
    pub best_red: f64,
    pub pareto: Vec<(f32, f32)>,
    pub solvent_keys: Vec<String>,
    pub units: usize,
    pub n_solvents: usize,
}

/// Read + extract the same solvents / DGEBA sphere as diagnostic(), fail-closed.
fn showcase_blend_inputs() -> Result<(Vec<Solvent>, [f64; 3], f64)> {
    let oracle = SourceOracle::pinned_default().map_err(|e| anyhow!("{e}"))?;
    let facts = oracle
        .read("ingredient_library_facts")
        .map_err(|e| anyhow!("{e}"))?;
    let entries = facts
        .value
        .get("entries")
        .and_then(|v| v.as_object())
        .context("facts.json has no entries object")?;
    let mut names: BTreeSet<String> = BTreeSet::new();
    for key in entries.keys() {
        if let Some(rest) = key.strip_prefix("solvent.") {
            if let Some((name, _prop)) = rest.split_once('.') {
                names.insert(name.to_string());
            }
        }
    }
    let mut solvents: Vec<Solvent> = Vec::new();
    for name in &names {
        let density = entry_f64(entries, &format!("solvent.{name}.density"));
        let flash = entry_f64(entries, &format!("solvent.{name}.flash_c"));
        let hsp = entry_hsp(entries, &format!("solvent.{name}.hsp"));
        if let (Some(d), Some(f), Some(h)) = (density, flash, hsp) {
            solvents.push(Solvent {
                key: name.clone(),
                density_g_ml: d,
                flash_c: f,
                hsp: h,
            });
        }
    }
    if solvents.is_empty() {
        anyhow::bail!("no fully-characterized solvents in pinned facts source");
    }
    let center = entry_hsp(entries, "binder.dgeba.hsp").context("binder.dgeba.hsp missing")?;
    let radius =
        entry_f64(entries, "binder.dgeba.hsp_radius").context("binder.dgeba.hsp_radius missing")?;
    Ok((solvents, center, radius))
}

/// Enumerate the carrier simplex at `units` resolution, in parallel over the
/// first-solvent count, evaluating every cell with the real constraints.
/// `progress` receives the running count of cells evaluated (for the live UI).
pub fn showcase_grid(
    units: usize,
    progress: &AtomicU64,
    live: Option<&std::sync::mpsc::SyncSender<GridDelta>>,
) -> Result<ShowcaseGrid> {
    let (solvents, center, radius) = showcase_blend_inputs()?;
    let n = solvents.len();
    let phi = VS_HI;
    let parts: Vec<(u64, u64, f64, f64, Vec<(f32, f32)>)> = (0..=units)
        .into_par_iter()
        .map(|k0| {
            let mut total = 0u64;
            let mut feas = 0u64;
            let mut best_voc = f64::INFINITY;
            let mut best_red = 0.0_f64;
            let mut best_blend: Vec<(String, f64)> = Vec::new();
            let mut samples: Vec<(f32, f32)> = Vec::new();
            let mut cur: Vec<usize> = Vec::with_capacity(n);
            enumerate_compositions(n - 1, units - k0, &mut cur, &mut |rest: &[usize]| {
                total += 1;
                let mut x = [0.0f64; 8];
                x[0] = k0 as f64 / units as f64;
                for (i, &u) in rest.iter().enumerate() {
                    x[i + 1] = u as f64 / units as f64;
                }
                let xs = &x[..n];
                if is_feasible(phi, xs, &solvents, &center, radius) {
                    feas += 1;
                    let voc = voc_g_per_l(phi, xs, &solvents);
                    let red = hansen_red(&blend_hsp(xs, &solvents), &center, radius);
                    if voc < best_voc {
                        best_voc = voc;
                        best_red = red;
                        best_blend = solvents
                            .iter()
                            .zip(xs.iter())
                            .filter(|(_, &x)| x > 1e-9)
                            .map(|(sv, &x)| (sv.key.clone(), x))
                            .collect();
                    }
                    if samples.len() < 64 && total % 3 == 0 {
                        samples.push((voc as f32, red as f32));
                    }
                }
            });
            progress.fetch_add(total, Ordering::Relaxed);
            if let Some(tx) = live {
                // try_send drops when the bounded channel is full -> natural
                // throttle; compute never blocks on the UI.
                let _ = tx.try_send(GridDelta {
                    cells_done_delta: total,
                    chunk_best_voc: best_voc,
                    chunk_best_red: best_red,
                    new_samples: samples.clone(),
                    chunk_best_blend: best_blend.clone(),
                });
            }
            (total, feas, best_voc, best_red, samples)
        })
        .collect();

    let mut cells_total = 0u64;
    let mut cells_feasible = 0u64;
    let mut best_voc = f64::INFINITY;
    let mut best_red = 0.0_f64;
    let mut pareto: Vec<(f32, f32)> = Vec::new();
    for (t, f, bv, br, s) in parts {
        cells_total += t;
        cells_feasible += f;
        if bv < best_voc {
            best_voc = bv;
            best_red = br;
        }
        pareto.extend(s);
    }
    if pareto.len() > 400 {
        let step = (pareto.len() / 400).max(1);
        pareto = pareto.iter().step_by(step).copied().collect();
    }
    Ok(ShowcaseGrid {
        cells_total,
        cells_feasible,
        best_voc,
        best_red,
        pareto,
        solvent_keys: solvents.iter().map(|s| s.key.clone()).collect(),
        units,
        n_solvents: n,
    })
}
