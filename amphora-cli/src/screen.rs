//! COMPOUNDS/SECOND screening example (E4). Enumerates genuinely-distinct,
//! rights-clean, RDKit-valid molecules and measures how fast the pinned RDKit
//! pipeline canonicalizes, fingerprints, and runs the deterministic diagnostic
//! modules over them. This is an ENGINEERING THROUGHPUT metric only -- not a
//! novelty score, ranking, screening quality, or validated science. Every
//! molecule module is ranking_eligible:false / AUDIT_ONLY.
use amphora_engine::{EnginePool, ScoreProgress};
use anyhow::{anyhow, Result};
use rayon::prelude::*;
use serde_json::{json, Value};
use std::collections::{BTreeMap, HashSet};
use std::path::Path;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Instant;

/// Substituent caps attached to the two backbone termini. All keep the molecule
/// single-fragment and wildcard-free: -H, -OH, -NH2, -OCH3, -O-glycidyl (epoxide),
/// -phenyl. Trivially rights-clean chemistry.
const CAPS: [&str; 6] = ["", "O", "N", "OC", "OCC1CO1", "c1ccccc1"];

fn assemble(n: usize, left: &str, right: &str, branch: usize) -> String {
    let mut s = String::with_capacity(left.len() + right.len() + n + 3);
    s.push_str(left);
    for i in 1..=n {
        s.push('C');
        if i == branch {
            s.push_str("(C)");
        }
    }
    s.push_str(right);
    s
}

fn role_for(left: &str, right: &str) -> &'static str {
    if left.contains("OCC1CO1") || right.contains("OCC1CO1") {
        "resin" // carries an oxirane
    } else if left == "N" || right == "N" {
        "hardener" // carries a primary amine
    } else {
        "resin"
    }
}

/// Deterministically enumerate `target` distinct compounds. Each candidate string
/// is validated through the real pinned RDKit backend (`molecule_facts`) and
/// deduplicated by `canonical_structure_sha256`, so the returned set is 100%
/// RDKit-valid and pairwise distinct. Requires the `rdkit` feature at runtime
/// (without it `molecule_facts` fails closed and this returns empty).
pub fn enumerate_distinct(target: usize, n_max: usize) -> Vec<(String, &'static str, String)> {
    let mut seen: HashSet<String> = HashSet::new();
    let mut out: Vec<(String, &'static str, String)> = Vec::with_capacity(target);
    for n in 2..=n_max {
        for &left in &CAPS {
            for &right in &CAPS {
                for branch in 0..=n {
                    let smiles = assemble(n, left, right, branch);
                    let Ok(facts) = amphora_rdkit_ffi::molecule_facts(&smiles) else {
                        continue;
                    };
                    if seen.insert(facts.canonical_structure_sha256.clone()) {
                        let id = format!("screen-{:06}", out.len());
                        out.push((id, role_for(left, right), facts.canonical_isomeric_smiles));
                        if out.len() == target {
                            return out;
                        }
                    }
                }
            }
        }
    }
    out
}

fn screen_candidate(id: &str, role: &str, smiles: &str) -> Value {
    json!({
        "candidate_id": id,
        "candidate_type": "molecule",
        "context": {"campaign_authority": "AUDIT_ONLY", "screening_probe": true},
        "evidence_refs": {},
        "molecule": {
            "role": role,
            "smiles": smiles,
            "source_status": "UNMADE_ENUMERATED_SCREENING_PROBE"
        }
    })
}

/// A structurally-admissible exemplar (passes ALL hard design gates). This is a
/// FILTER result, never a ranking: molecule modules are AUDIT_ONLY /
/// ranking_eligible:false and expose no score. Selected quality-neutrally (the
/// lexicographically-smallest canonical structure hash among admissible ones).
#[derive(Default, Clone)]
pub struct Exemplar {
    pub found: bool,
    pub smiles: String,
    pub formula: String,
    pub mw: f64,
    pub role: String,
    pub eew: Option<f64>,
    pub ahew: Option<f64>,
    pub novelty_dist: Option<f64>,
}

fn envelope<'a>(v: &'a Value, module_id: &str) -> Option<&'a Value> {
    v.pointer("/score_envelopes")?
        .as_array()?
        .iter()
        .find(|e| e.get("module_id").and_then(Value::as_str) == Some(module_id))
}

pub struct ScreenOutcome {
    pub target: usize,
    pub scored_ok: usize,
    pub distinct: usize,
    pub all_normalized: bool,
    pub optimizer_admissible: usize,
    pub workers: usize,
    pub elapsed_s: f64,
    pub compounds_per_s: f64,
    pub exemplar: Exemplar,
    /// Real per-module invocation tally over the batch: (module_id, scored, total).
    pub module_scored: Vec<(String, u64, u64)>,
}

/// Full-score throughput: build one CandidateEnvelope per distinct compound and
/// run the whole engine scoring path in parallel. `on_progress(completed)` is
/// called from worker threads (touches only an atomic; never the results), so
/// results are bit-identical to a no-callback run.
pub fn run_screen(
    root: &Path,
    compounds: &[(String, &'static str, String)],
    workers: usize,
    on_progress: impl Fn(u64) + Sync,
) -> Result<ScreenOutcome> {
    let pool = EnginePool::new(root, workers)?;
    let requests: Vec<(Value, u64, Value, String)> = compounds
        .iter()
        .map(|(id, role, smi)| {
            (screen_candidate(id, role, smi), 42u64, json!({}), format!("screen-{id}"))
        })
        .collect();
    let started = Instant::now();
    let results = pool.score_many_with_progress(requests, |p: ScoreProgress| {
        on_progress(p.completed as u64);
    });
    let elapsed = started.elapsed();

    let mut scored_ok = 0usize;
    let mut all_normalized = true;
    let mut optimizer_admissible = 0usize;
    let mut distinct: HashSet<String> = HashSet::new();
    let mut best_hash: Option<String> = None;
    let mut exemplar = Exemplar::default();
    let mut modstat: BTreeMap<String, (u64, u64)> = BTreeMap::new();
    for row in &results {
        match row {
            Ok((value, _)) => {
                scored_ok += 1;
                let status = value
                    .pointer("/candidate/normalized_molecule/normalization/status")
                    .and_then(Value::as_str)
                    .unwrap_or("");
                if status != "NORMALIZED" {
                    all_normalized = false;
                }
                if let Some(h) = value
                    .pointer("/candidate/normalized_molecule/normalization/canonical_structure_hash")
                    .and_then(Value::as_str)
                {
                    distinct.insert(h.to_string());
                }
                if let Some(envs) = value.pointer("/score_envelopes").and_then(Value::as_array) {
                    if envs.iter().any(|e| {
                        e.get("usable_by_optimizer").and_then(Value::as_bool) == Some(true)
                    }) {
                        optimizer_admissible += 1;
                    }
                    for e in envs {
                        if let Some(mid) = e.get("module_id").and_then(Value::as_str) {
                            let ent = modstat.entry(mid.to_string()).or_insert((0, 0));
                            ent.1 += 1;
                            if e.get("status").and_then(Value::as_str) == Some("SCORED") {
                                ent.0 += 1;
                            }
                        }
                    }
                }
                // Admissible-exemplar FILTER (not a sort): keep only compounds
                // that pass ALL hard design gates, then select the one with the
                // lexicographically smallest canonical hash -- quality-neutral.
                let pass_all_hard = envelope(value, "amphora-molecule-design-gate")
                    .and_then(|e| e.pointer("/gates/pass_all_hard"))
                    .and_then(Value::as_bool)
                    == Some(true);
                if pass_all_hard {
                    if let Some(hash) = value
                        .pointer("/candidate/normalized_molecule/normalization/canonical_structure_hash")
                        .and_then(Value::as_str)
                    {
                        let better = match &best_hash {
                            None => true,
                            Some(h) => hash < h.as_str(),
                        };
                        if better {
                            best_hash = Some(hash.to_string());
                            let facts = value
                                .pointer("/candidate/normalized_molecule/normalization/molecule_facts_v1");
                            let f = |k: &str| facts.and_then(|x| x.get(k)).and_then(Value::as_f64);
                            let sv = |ptr: &str| value.pointer(ptr).and_then(Value::as_str).unwrap_or("").to_string();
                            let prop = envelope(value, "amphora-molecule-property");
                            let eew = prop.and_then(|e| e.pointer("/metrics/property_results/eew_g_per_eq")).and_then(Value::as_f64);
                            let ahew = prop.and_then(|e| e.pointer("/metrics/property_results/ahew_g_per_eq")).and_then(Value::as_f64);
                            let novelty_dist = envelope(value, "amphora-molecule-novelty")
                                .and_then(|e| e.pointer("/metrics/novelty_score"))
                                .and_then(Value::as_f64);
                            exemplar = Exemplar {
                                found: true,
                                smiles: sv("/candidate/normalized_molecule/normalization/molecule_facts_v1/canonical_isomeric_smiles"),
                                formula: facts.and_then(|x| x.get("formula")).and_then(Value::as_str).unwrap_or("").to_string(),
                                mw: f("average_molecular_weight_g_mol").unwrap_or(0.0),
                                role: sv("/candidate/normalized_molecule/molecule/role"),
                                eew,
                                ahew,
                                novelty_dist,
                            };
                        }
                    }
                }
            }
            Err(_) => all_normalized = false,
        }
    }
    let secs = elapsed.as_secs_f64().max(1e-9);
    Ok(ScreenOutcome {
        target: compounds.len(),
        scored_ok,
        distinct: distinct.len(),
        all_normalized,
        optimizer_admissible,
        workers,
        elapsed_s: secs,
        compounds_per_s: scored_ok as f64 / secs,
        exemplar,
        module_scored: modstat.into_iter().map(|(k, (sc, tot))| (k, sc, tot)).collect(),
    })
}

/// Pre-screen throughput: canonicalize + fingerprint only (2 RDKit calls), no
/// engine, no gates, no envelope hashing. A different, larger, honestly-labelled
/// number: molecules canonicalized+fingerprinted per second.
pub fn prescreen(smiles: &[String], workers: usize) -> (usize, f64, f64) {
    let done = AtomicU64::new(0);
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(workers.max(1))
        .build()
        .expect("rayon pool");
    let started = Instant::now();
    let ok = pool.install(|| {
        smiles
            .par_iter()
            .filter(|s| {
                let r = amphora_rdkit_ffi::molecule_facts(s).is_ok()
                    && amphora_rdkit_ffi::morgan_fingerprint(s).is_ok();
                done.fetch_add(1, Ordering::Relaxed);
                r
            })
            .count()
    });
    let secs = started.elapsed().as_secs_f64().max(1e-9);
    (ok, secs, ok as f64 / secs)
}

/// CLI entry point for a headless throughput measurement.
pub fn run_cli(root: &Path, target: usize, workers: usize, n_max: usize, do_prescreen: bool) -> Result<()> {
    eprintln!("enumerating {target} distinct compounds (n_max={n_max}) …");
    let compounds = enumerate_distinct(target, n_max);
    if compounds.is_empty() {
        return Err(anyhow!(
            "enumeration produced 0 compounds — the pinned RDKit backend is required (build --features rdkit)"
        ));
    }
    let completed = AtomicU64::new(0);
    let outcome = run_screen(root, &compounds, workers, |c| {
        completed.store(c, Ordering::Relaxed);
    })?;

    // Fail-closed honesty gates.
    if outcome.distinct != outcome.scored_ok {
        return Err(anyhow!(
            "distinctness gate FAILED: {} scored but only {} distinct structures",
            outcome.scored_ok,
            outcome.distinct
        ));
    }
    if outcome.optimizer_admissible != 0 {
        return Err(anyhow!(
            "honesty gate FAILED: {} candidates marked usable_by_optimizer (must be 0)",
            outcome.optimizer_admissible
        ));
    }

    println!("COMPOUNDS/SECOND — engineering throughput only (not novelty/ranking/validated science)");
    println!("  compounds enumerated : {}", outcome.target);
    println!("  fully gate-scored    : {}", outcome.scored_ok);
    println!("  distinct structures  : {}  (== scored: {})", outcome.distinct, outcome.distinct == outcome.scored_ok);
    println!("  all NORMALIZED       : {}", outcome.all_normalized);
    println!("  optimizer-admissible : {}  (must be 0)", outcome.optimizer_admissible);
    println!("  workers              : {}", outcome.workers);
    println!("  elapsed              : {:.2}s", outcome.elapsed_s);
    println!("  >> COMPOUNDS/SEC     : {:.0}", outcome.compounds_per_s);
    if outcome.exemplar.found {
        let e = &outcome.exemplar;
        println!("  admissible exemplar  : {} ({}) role={} MW={:.1} eew={:?} ahew={:?} novelty_dist={:?}",
            e.smiles, e.formula, e.role, e.mw, e.eew, e.ahew, e.novelty_dist);
        println!("    (passes all hard design gates; structural applicability only, NOT ranked/validated)");
    }

    if do_prescreen {
        let smiles: Vec<String> = compounds.iter().map(|(_, _, s)| s.clone()).collect();
        let (ok, secs, mps) = prescreen(&smiles, workers);
        println!("  pre-screen (canonicalize+fingerprint only, {ok} molecules, {:.2}s)", secs);
        println!("  >> MOLECULES/SEC     : {:.0}", mps);
    }
    Ok(())
}
