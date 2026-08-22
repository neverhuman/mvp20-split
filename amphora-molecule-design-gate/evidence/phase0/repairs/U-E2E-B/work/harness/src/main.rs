//! U-E2E-B ranking harness: genuinely invokes amphora-solver-lab's
//! deterministic NSGA-II (src/nsga2.rs, pinned splitmix64 seed) to rank the
//! U-E2E survivor candidate set on the only two live numeric evaluator
//! families this candidate set actually has (property EEW/AHEW, novelty).
//! amphora-solver-lab's authority stays AUDIT_ONLY -- this harness reads its
//! public `nsga2::run` entry point exactly as amphora-solver-lab's own P1
//! demo (src/demos/p1.rs) does, and grants no promotion authority itself.
//!
//! Because there is no continuous mixing variable for discrete candidate
//! selection, ranking is implemented as a 1-gene real-valued NSGA-II problem
//! (gene in [0, n-1]) whose eval() rounds the gene to the nearest candidate
//! index -- the same "vertex-seeded" pattern p1.rs uses for pure-solvent
//! blends, specialized to n=1 gene. Every candidate index is also seeded
//! directly into generation 0 so the front cannot omit a true Pareto point
//! for lack of exploration. An independent O(n^2) brute-force dominance
//! check over the same fixed points cross-verifies the NSGA-II front.

use amphora_solver_lab::nsga2::{self, Nsga2Config};
use serde::Deserialize;
use serde_json::json;
use std::collections::BTreeSet;
use std::env;
use std::fs;

/// Same pinned seed amphora-solver-lab/src/demos/p1.rs uses (NSGA_SEED =
/// 0x2026_0803); reused here rather than minted fresh, per the crate's own
/// "pinned splitmix64 seed" determinism convention.
const NSGA_SEED: u64 = 0x2026_0803;

#[derive(Deserialize, Clone)]
struct Survivor {
    candidate_id: String,
    novelty_score: f64,
    ahew_g_per_eq: f64,
}

fn main() {
    let args: Vec<String> = env::args().collect();
    assert_eq!(args.len(), 3, "usage: harness <survivors_input.json> <diagnostic_out.json>");
    let input_path = &args[1];
    let output_path = &args[2];

    let raw = fs::read_to_string(input_path).expect("read survivors_input.json");
    let survivors: Vec<Survivor> = serde_json::from_str(&raw).expect("parse survivors_input.json");
    let n = survivors.len();
    assert!(n >= 2, "need >=2 survivors to run a multi-objective front");

    let cfg = Nsga2Config {
        pop_size: 40,
        generations: 200,
        seed: NSGA_SEED,
        eta_crossover: 15.0,
        eta_mutation: 20.0,
        p_crossover: 0.9,
        p_mutation: 1.0,
        gene_lo: 0.0,
        gene_hi: (n - 1) as f64,
    };

    let vertex_seeds: Vec<Vec<f64>> = (0..n).map(|i| vec![i as f64]).collect();

    let survivors_ea = survivors.clone();
    let front = nsga2::run(&cfg, 1, &vertex_seeds, move |genes: &[f64]| {
        let idx = genes[0].round().clamp(0.0, (n - 1) as f64) as usize;
        let s = &survivors_ea[idx];
        // minimize (-novelty_score, ahew_g_per_eq) == maximize novelty, minimize AHEW.
        (vec![-s.novelty_score, s.ahew_g_per_eq], 0.0)
    });

    let mut seen: BTreeSet<usize> = BTreeSet::new();
    let mut ranked: Vec<serde_json::Value> = Vec::new();
    for ind in &front {
        let idx = ind.genes[0].round().clamp(0.0, (n - 1) as f64) as usize;
        if seen.insert(idx) {
            let s = &survivors[idx];
            ranked.push(json!({
                "candidate_id": s.candidate_id,
                "novelty_score": s.novelty_score,
                "ahew_g_per_eq": s.ahew_g_per_eq,
                "nsga2_objectives_minimized": [-s.novelty_score, s.ahew_g_per_eq],
            }));
        }
    }

    // Independent O(n^2) brute-force Pareto front over the same fixed points,
    // computed without touching nsga2.rs, as a cross-method agreement gate.
    let dominates = |a: (f64, f64), b: (f64, f64)| -> bool {
        (a.0 <= b.0 && a.1 <= b.1) && (a.0 < b.0 || a.1 < b.1)
    };
    let objs: Vec<(f64, f64)> = survivors.iter().map(|s| (-s.novelty_score, s.ahew_g_per_eq)).collect();
    let mut brute_idx: Vec<usize> = Vec::new();
    for i in 0..n {
        let mut dominated = false;
        for j in 0..n {
            if i != j && dominates(objs[j], objs[i]) {
                dominated = true;
                break;
            }
        }
        if !dominated {
            brute_idx.push(i);
        }
    }
    let brute_set: BTreeSet<usize> = brute_idx.iter().cloned().collect();
    let agree = brute_set == seen;

    let out = json!({
        "schema": "amphora.molecule-design-gate.u-e2e-b-nsga2-ranking-diagnostic.v1",
        "n_survivors_ranked": n,
        "nsga2_config": {
            "pop_size": cfg.pop_size,
            "generations": cfg.generations,
            "seed_hex": format!("{:#x}", cfg.seed),
            "eta_crossover": cfg.eta_crossover,
            "eta_mutation": cfg.eta_mutation,
            "p_crossover": cfg.p_crossover,
            "p_mutation": cfg.p_mutation,
            "gene_lo": cfg.gene_lo,
            "gene_hi": cfg.gene_hi,
        },
        "objective_definition": {
            "objective_0": "minimize(-novelty_score), i.e. maximize novelty_score (Tanimoto-distance novelty vs the frozen Phase-0 novelty-corpus.v1.json, U-E2E's live novelty evaluator cell)",
            "objective_1": "minimize(ahew_g_per_eq) (amine hydrogen equivalent weight, U-E2E's live property-evaluator cell)",
            "caveat": "The 'lower ahew_g_per_eq is better' direction is an illustrative convention chosen for this fire to exercise NSGA-II mechanics on the only two live numeric evaluator families this candidate set has (2 of 6 families); it is NOT a portfolio-endorsed design objective. The ranking is AUDIT_ONLY / non-promoting regardless of the direction chosen; amphora-solver-lab's own authority ceiling is unaffected."
        },
        "pareto_front_nsga2": ranked,
        "brute_force_cross_check": {
            "method": "O(n^2) exhaustive pairwise dominance over the same n fixed (candidate_id, -novelty_score, ahew_g_per_eq) points, computed independently of nsga2::run in this same binary",
            "brute_force_front_indices": brute_idx,
            "nsga2_front_indices": seen.iter().cloned().collect::<Vec<usize>>(),
            "sets_agree": agree,
        },
    });

    fs::write(output_path, serde_json::to_string_pretty(&out).unwrap()).expect("write diagnostic output");
    if !agree {
        eprintln!("FATAL: nsga2 front and brute-force front disagree -- refusing to treat ranking as trustworthy");
        std::process::exit(1);
    }
}
