mod compound;
mod control;
mod dashboard;
mod phase0;
mod phase1;

use amphora_core::{
    apply_rank_deltas, collect_claim_locks, make_score_history, now_ms, rank_candidates,
    stable_hash, verify_run, CandidateRecord, CandidateStatus, KpiProfile, ModuleTelemetry,
    RankedCandidate, RunArchive, ScoreHistory, Throughput,
};
use amphora_engine::EnginePool;
use amphora_tui::{run_live_dashboard, state_text, DashboardState};
use anyhow::{anyhow, Context, Result};
use clap::{Args, Parser, Subcommand, ValueEnum};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::fs;
use std::io::{self, IsTerminal, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::Sender;
use std::sync::Arc;
use std::thread;

#[derive(Parser, Debug)]
#[command(
    name = "amphora-tui",
    version,
    about = "Amphora MVP20 evolutionary control plane"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand, Debug)]
enum Command {
    Compound(compound::CompoundArgs),
    Data(control::DataArgs),
    Benchmark(control::BenchmarkArgs),
    Portfolio(control::PortfolioArgs),
    Shadow(control::ShadowArgs),
    PotLife(control::PotLifeArgs),
    Model(control::ModelArgs),
    Demo(RunArgs),
    Run(RunArgs),
    Inspect(InspectArgs),
    Replay(ReplayArgs),
    Resume {
        #[arg(long)]
        run: PathBuf,
    },
    Export {
        #[arg(long)]
        run: PathBuf,
        #[arg(long, value_enum, default_value_t = ExportFormat::Json)]
        format: ExportFormat,
    },
}

#[derive(ValueEnum, Debug, Clone)]
enum ExportFormat {
    Json,
    Jsonl,
}

#[derive(Args, Debug, Clone)]
struct RunArgs {
    #[arg(long)]
    candidate: Option<PathBuf>,
    #[arg(long, default_value_t = 25)]
    population: usize,
    #[arg(long, default_value_t = 2)]
    generations: u32,
    #[arg(long, default_value_t = 2)]
    workers: usize,
    #[arg(long, default_value_t = 42)]
    seed: u64,
    #[arg(long, default_value_t = 100)]
    refresh_ms: u64,
    #[arg(long)]
    objective_profile: Option<PathBuf>,
    #[arg(long, default_value = "molecule")]
    lane: String,
    #[arg(long)]
    headless: bool,
    #[arg(long)]
    jsonl: bool,
}

#[derive(Args, Debug)]
struct InspectArgs {
    #[arg(long)]
    candidate: PathBuf,
    #[arg(long, default_value = "molecule")]
    lane: String,
    #[arg(long)]
    headless: bool,
}

#[derive(Args, Debug)]
struct ReplayArgs {
    #[arg(long)]
    run: Option<PathBuf>,
    #[arg(long)]
    verify: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct RunState {
    schema: String,
    run_id: String,
    generation: u32,
    generations: u32,
    #[serde(default = "default_phase")]
    phase: String,
    #[serde(default)]
    scoring_completed: usize,
    #[serde(default)]
    scoring_total: usize,
    #[serde(default)]
    rejected_candidates: u64,
    #[serde(default)]
    worker_failures: u64,
    throughput: Throughput,
    active_workers: usize,
    registered_modules: usize,
    active_modules: usize,
    modules: Vec<ModuleTelemetry>,
    candidates: Vec<RankedCandidate>,
    history: Vec<ScoreHistory>,
    records: Vec<CandidateRecord>,
    objective_ready: bool,
    finished: bool,
    logs: Vec<String>,
}

impl RunState {
    fn dashboard(&self) -> DashboardState {
        DashboardState {
            run_id: self.run_id.clone(),
            generation: self.generation,
            generations: self.generations,
            phase: self.phase.clone(),
            scoring_completed: self.scoring_completed,
            scoring_total: self.scoring_total,
            rejected_candidates: self.rejected_candidates,
            worker_failures: self.worker_failures,
            elapsed_ms: now_ms().saturating_sub(self.throughput.started_at_ms),
            throughput: self.throughput.clone(),
            active_workers: self.active_workers,
            registered_modules: self.registered_modules,
            active_modules: self.active_modules,
            modules: self.modules.clone(),
            candidates: self.candidates.clone(),
            history: self.history.clone(),
            selected_candidate: self.candidates.first().map(|c| c.candidate_id.clone()),
            paused: false,
            objective_ready: self.objective_ready,
            finished: self.finished,
            logs: self.logs.clone(),
        }
    }
}

fn default_phase() -> String {
    "INITIALIZING".into()
}

fn workspace_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf()
}

fn read_json(path: &Path) -> Result<Value> {
    let bytes = fs::read(path).with_context(|| format!("reading {}", path.display()))?;
    amphora_core::parse_json_strict(&bytes).map_err(Into::into)
}

fn raw_file_sha256(path: &Path) -> Result<String> {
    let bytes = fs::read(path).with_context(|| format!("hashing {}", path.display()))?;
    let mut digest = Sha256::new();
    digest.update(bytes);
    Ok(format!("{:x}", digest.finalize()))
}

fn demo_candidate(root: &Path) -> Result<Value> {
    read_json(&root.join("amphora-candidate-contract/fixtures/molecule_candidate.json"))
}

fn load_profile(root: &Path, requested: Option<&Path>) -> Result<KpiProfile> {
    let path = requested
        .map(PathBuf::from)
        .unwrap_or_else(|| root.join("config/kpis/molecule-demo.json"));
    let profile: KpiProfile = serde_json::from_value(read_json(&path)?)?;
    let has_design_gate = profile.hard_constraints.iter().any(|constraint| {
        constraint.module_id == "amphora-molecule-design-gate"
            && constraint.section == "gates"
            && constraint.path == "pass_all_hard"
            && constraint.operator == "=="
            && constraint.expected == Value::Bool(true)
    });
    if !has_design_gate {
        return Err(anyhow!(
            "live molecule KPI profile must include amphora-molecule-design-gate.gates.pass_all_hard == true"
        ));
    }
    Ok(profile)
}

fn inject_profile(mut candidate: Value, profile: &KpiProfile) -> Value {
    let Some(object) = candidate.as_object_mut() else {
        return candidate;
    };
    let context = object.entry("context").or_insert_with(|| json!({}));
    let Some(context) = context.as_object_mut() else {
        return candidate;
    };
    let declarations: Vec<Value> = profile.objectives.iter().map(|objective| json!({
        "id": objective.id, "module_id": objective.module_id, "section": objective.section, "path": objective.path,
        "label": objective.label, "direction": objective.direction, "unit": objective.unit,
    })).collect();
    let hard_constraints: Vec<Value> = profile.hard_constraints.iter().map(|constraint| json!({
        "id": constraint.id, "module_id": constraint.module_id, "section": constraint.section,
        "path": constraint.path, "label": constraint.label, "operator": constraint.operator,
        "expected": constraint.expected,
    })).collect();
    let request = context
        .entry("optimization_request")
        .or_insert_with(|| json!({}));
    if let Some(request) = request.as_object_mut() {
        request.insert("objective_list".into(), Value::Array(declarations));
        request.insert("hard_constraints".into(), Value::Array(hard_constraints));
    }
    candidate
}

fn lineage(candidate: &Value, generation: u32, mutation_id: Option<&str>) -> Value {
    json!({"parent_ids": candidate.get("lineage").and_then(|l| l.get("parent_ids")).cloned().unwrap_or_else(|| json!([])), "generation": generation, "mutation_id": mutation_id})
}

fn record_from(
    candidate: &Value,
    result: &Value,
    generation: u32,
    status: CandidateStatus,
) -> CandidateRecord {
    let id = candidate
        .get("candidate_id")
        .and_then(Value::as_str)
        .unwrap_or("unknown")
        .to_string();
    // T-01B: read only host-owned identity paths, never a caller-echoed key.
    // Molecule identity lives under the host-written `normalization` object;
    // formulation identity is the host-overwritten top-level `formula_hash`.
    let hash = result
        .pointer("/candidate/normalized_molecule/normalization/canonical_structure_hash")
        .or_else(|| result.pointer("/candidate/normalized_formulation/formula_hash"))
        .and_then(Value::as_str)
        .map(str::to_string);
    let parent_ids = candidate
        .pointer("/lineage/parent_ids")
        .and_then(Value::as_array)
        .map(|rows| {
            rows.iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect()
        })
        .unwrap_or_default();
    let mutation_id = candidate
        .pointer("/lineage/mutation_id")
        .and_then(Value::as_str)
        .map(str::to_string);
    let result_hash = result
        .pointer("/provenance/result_hash")
        .and_then(Value::as_str)
        .map(str::to_string);
    CandidateRecord {
        candidate_id: id,
        candidate_type: candidate
            .get("candidate_type")
            .and_then(Value::as_str)
            .unwrap_or("unknown")
            .into(),
        candidate: candidate.clone(),
        canonical_structure_hash: hash,
        parent_ids,
        generation,
        mutation_id,
        lifecycle_status: status,
        result_hash,
        objective_rows: Vec::new(),
        hard_constraint_pass: None,
        claim_locks: collect_claim_locks(result),
    }
}

fn envelope_telemetry(modules: &mut [ModuleTelemetry], result: &Value, elapsed_ms: u64) {
    let envelopes = result.pointer("/score_envelopes").and_then(Value::as_array);
    for module in modules.iter_mut() {
        if let Some(envelope) = envelopes.and_then(|rows| {
            rows.iter().find(|row| {
                row.get("module_id").and_then(Value::as_str) == Some(module.module_id.as_str())
            })
        }) {
            module.authority_tier = envelope
                .get("authority_tier")
                .and_then(Value::as_str)
                .unwrap_or("UNKNOWN")
                .into();
            module.readiness = envelope
                .pointer("/metrics/model_card/model_readiness_status")
                .and_then(Value::as_str)
                .unwrap_or("UNKNOWN")
                .into();
            module.record(
                envelope
                    .get("status")
                    .and_then(Value::as_str)
                    .unwrap_or("ERROR"),
                envelope.get("score_0_1").and_then(Value::as_f64),
                elapsed_ms,
            );
        }
    }
}

fn sync_records(state: &mut RunState) {
    for record in &mut state.records {
        if let Some(ranked) = state
            .candidates
            .iter()
            .find(|candidate| candidate.candidate_id == record.candidate_id)
        {
            record.objective_rows = ranked.objective_rows.clone();
            record.hard_constraint_pass = Some(ranked.feasible);
            record.lifecycle_status = if ranked.ranked {
                CandidateStatus::Ranked
            } else {
                CandidateStatus::Scored
            };
        }
    }
}

fn event_output(event: &amphora_core::Event, jsonl: bool) -> Result<()> {
    if jsonl {
        println!("{}", serde_json::to_string(event)?);
        io::stdout().flush()?;
    }
    Ok(())
}

fn add_event(
    archive: &mut RunArchive,
    event_type: &str,
    candidate_id: Option<String>,
    generation: u32,
    payload: Value,
    jsonl: bool,
) -> Result<()> {
    let event = archive.append(event_type, candidate_id, generation, payload)?;
    event_output(&event, jsonl)
}

fn progress(state: &mut RunState, message: impl Into<String>) {
    let message = message.into();
    state.logs.push(message);
    if state.logs.len() > 50 {
        state.logs.remove(0);
    }
}

fn publish(sender: &Option<Sender<DashboardState>>, state: &RunState) {
    if let Some(sender) = sender {
        let _ = sender.send(state.dashboard());
    }
}

fn score_batch(
    pool: &EnginePool,
    requests: Vec<(Value, u64, Value, String)>,
    phase: &str,
    state: &mut RunState,
    sender: &Option<Sender<DashboardState>>,
) -> Result<Vec<Result<(Value, u64)>>> {
    state.phase = phase.into();
    state.scoring_completed = 0;
    state.scoring_total = requests.len();
    publish(sender, state);
    let (progress_sender, progress_receiver) = std::sync::mpsc::channel();
    let results = std::thread::scope(|scope| {
        let handle = scope.spawn(move || {
            pool.score_many_with_progress(requests, |progress| {
                let _ = progress_sender.send(progress);
            })
        });
        while let Ok(update) = progress_receiver.recv() {
            state.scoring_completed = state.scoring_completed.max(update.completed);
            if !update.succeeded {
                state.worker_failures += 1;
            }
            publish(sender, state);
        }
        handle
            .join()
            .map_err(|_| anyhow!("scoring thread panicked"))
    })?;
    Ok(results)
}

fn run(args: RunArgs, root: &Path, demo: bool) -> Result<()> {
    let interactive = !args.headless && !args.jsonl && io::stdout().is_terminal();
    if !interactive {
        return run_solver(args, root, demo, None, Arc::new(AtomicBool::new(false)));
    }
    let refresh_ms = args.refresh_ms;
    let root = root.to_path_buf();
    let cancel = Arc::new(AtomicBool::new(false));
    let solver_cancel = Arc::clone(&cancel);
    let (sender, receiver) = std::sync::mpsc::channel();
    let solver = thread::spawn(move || run_solver(args, &root, demo, Some(sender), solver_cancel));
    let dashboard_result = run_live_dashboard(receiver, Arc::clone(&cancel), refresh_ms);
    let solver_result = solver
        .join()
        .map_err(|_| anyhow!("solver thread panicked"))?;
    dashboard_result?;
    solver_result
}

fn deterministic_run_id(
    candidate: &Value,
    seed: u64,
    population: usize,
    generations: u32,
    workers: usize,
    lane: &str,
    profile_id: &str,
) -> String {
    format!(
        "run-{}",
        &stable_hash(&json!({
            "candidate": candidate,
            "seed": seed,
            "population": population,
            "generations": generations,
            "workers": workers,
            "lane": lane,
            "objective_profile": profile_id,
            "runtime_contract": "amphora-digital-phase1-v1",
        }))[..20]
    )
}

fn run_solver(
    args: RunArgs,
    root: &Path,
    demo: bool,
    sender: Option<Sender<DashboardState>>,
    cancel: Arc<AtomicBool>,
) -> Result<()> {
    if args.lane != "molecule" {
        return Err(anyhow!(
            "only the molecule lane is live; formulation mode is inspect-only"
        ));
    }
    let profile = load_profile(root, args.objective_profile.as_deref())?;
    let candidate_path = args.candidate.clone().or_else(|| {
        if demo {
            None
        } else {
            Some(PathBuf::from("candidate.json"))
        }
    });
    let candidate = inject_profile(
        match candidate_path {
            Some(path) => read_json(&path)?,
            None => demo_candidate(root)?,
        },
        &profile,
    );
    let scoring_run_id = deterministic_run_id(
        &candidate,
        args.seed,
        args.population,
        args.generations,
        args.workers,
        &args.lane,
        &profile.profile_id,
    );
    let run_id = if demo {
        scoring_run_id.clone()
    } else {
        format!("run-{}", now_ms())
    };
    let pool = EnginePool::new(root, args.workers)?;
    let registry = pool.registry(&args.lane)?;
    let active_ids: Vec<String> = registry
        .get("active_submodels")
        .and_then(Value::as_array)
        .map(|rows| {
            rows.iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect()
        })
        .unwrap_or_default();
    let modules: Vec<_> = active_ids
        .iter()
        .map(|id| ModuleTelemetry::new(id.clone()))
        .collect();
    let executable = std::env::current_exe().context("resolving current executable")?;
    let manifest = json!({
        "schema":"amphora.run-manifest.v1",
        "run_id":run_id,
        "source": {
            "module_manifest_sha256": raw_file_sha256(&root.join("module-manifest.json"))?,
            "cargo_manifest_sha256": raw_file_sha256(&root.join("Cargo.toml"))?,
        },
        "binaries": {
            "amphora_cli_sha256": raw_file_sha256(&executable)?,
            "amphora_cli_path": executable,
        },
        "dependencies": {
            "cargo_lock_sha256": raw_file_sha256(&root.join("Cargo.lock"))?,
            "rust_package_version": env!("CARGO_PKG_VERSION"),
        },
        "data": {
            "feedback_build_manifest_sha256": raw_file_sha256(&root.join("feedback/v1/derived/build_manifest.json"))?,
        },
        "models": {},
        "configuration": {
            "objective_profile_hash": stable_hash(&serde_json::to_value(&profile)?),
            "registry_hash": stable_hash(&registry),
            "lane": args.lane,
            "population": args.population,
            "generations": args.generations,
            "workers": args.workers,
        },
        "rng": {
            "algorithm": "sha256-counter-v1",
            "seed": args.seed,
        },
        "inputs": {
            "candidate_contract_value_hash": stable_hash(&candidate),
        },
        "outputs": ["events.jsonl", "final-state.json", "provenance.json"],
        "objective_profile":profile.profile_id,
        "registry":registry,
    });
    let archive_path = Path::new(".amphora/runs").join(&run_id);
    if archive_path.exists() {
        let root_hash = verify_run(&archive_path)?;
        if args.jsonl {
            println!(
                "{}",
                serde_json::to_string(&json!({
                    "schema": "amphora.run-replay.v1",
                    "run_id": run_id,
                    "root_hash": root_hash,
                    "immutable_existing_run": true,
                }))?
            );
        } else {
            println!("verified immutable run {run_id}: {root_hash}");
        }
        return Ok(());
    }
    let mut archive = RunArchive::create(".amphora/runs", &run_id, &manifest)?;
    let mut state = RunState {
        schema: "amphora.rust-state.v1".into(),
        run_id: run_id.clone(),
        generation: 0,
        generations: args.generations,
        phase: "INITIALIZING".into(),
        scoring_completed: 0,
        scoring_total: 0,
        rejected_candidates: 0,
        worker_failures: 0,
        throughput: Throughput::default(),
        active_workers: args.workers.max(1),
        registered_modules: registry
            .get("module_count")
            .and_then(Value::as_u64)
            .unwrap_or(0) as usize,
        active_modules: active_ids.len(),
        modules,
        candidates: Vec::new(),
        history: Vec::new(),
        records: Vec::new(),
        objective_ready: false,
        finished: false,
        logs: Vec::new(),
    };
    add_event(
        &mut archive,
        "run_started",
        None,
        0,
        json!({"seed":args.seed,"population":args.population}),
        args.jsonl,
    )?;
    let registered_modules = state.registered_modules;
    progress(
        &mut state,
        format!(
            "run {} started: generation 0/{} | population {} | workers {} | active submodels {}/{}",
            run_id,
            args.generations,
            args.population,
            args.workers,
            active_ids.len(),
            registered_modules
        ),
    );
    add_event(
        &mut archive,
        "registry_loaded",
        None,
        0,
        registry.clone(),
        args.jsonl,
    )?;
    publish(&sender, &state);
    if cancel.load(Ordering::SeqCst) {
        return Ok(());
    }

    let mut scored: Vec<(Value, Value)> = Vec::new();
    let mut current: Vec<(Value, Value)> = Vec::new();
    state.phase = "PROPOSING".into();
    state.scoring_completed = 0;
    state.scoring_total = 0;
    publish(&sender, &state);
    let mut proposals: Vec<Value> = vec![candidate.clone()];
    for index in 1..args.population.max(1) {
        match pool.mutate(
            &candidate,
            args.seed + index as u64,
            json!({"parent_ids":[candidate["candidate_id"]],"generation":1,"mutation_id":null}),
        ) {
            Ok(offspring) => proposals.push(offspring),
            Err(error) => {
                state.rejected_candidates += 1;
                add_event(
                    &mut archive,
                    "candidate_rejected",
                    candidate
                        .get("candidate_id")
                        .and_then(Value::as_str)
                        .map(str::to_string),
                    1,
                    json!({"reason":error.to_string(),"proposal_seed":args.seed + index as u64}),
                    args.jsonl,
                )?;
                publish(&sender, &state);
            }
        }
    }
    let initial_requests: Vec<_> = proposals
        .iter()
        .enumerate()
        .map(|(index, proposal)| {
            (
                proposal.clone(),
                args.seed + index as u64,
                lineage(
                    proposal,
                    0,
                    proposal
                        .pointer("/lineage/mutation_id")
                        .and_then(Value::as_str),
                ),
                scoring_run_id.clone(),
            )
        })
        .collect();
    progress(
        &mut state,
        format!(
            "generation 0/{}: scoring {}/{} valid candidates",
            args.generations,
            initial_requests.len(),
            args.population.max(1)
        ),
    );
    let initial_results = score_batch(
        &pool,
        initial_requests,
        "SCORING_INITIAL_POPULATION",
        &mut state,
        &sender,
    )?;
    for (index, (proposal, scored_result)) in proposals.into_iter().zip(initial_results).enumerate()
    {
        let id = proposal
            .get("candidate_id")
            .and_then(Value::as_str)
            .map(str::to_string);
        add_event(
            &mut archive,
            "candidate_proposed",
            id.clone(),
            0,
            json!({"candidate":proposal}),
            args.jsonl,
        )?;
        state.throughput.sample(1, 1, 0, 0, 0);
        match scored_result {
            Ok((result, elapsed)) => {
                let row = record_from(&proposal, &result, 0, CandidateStatus::Scored);
                envelope_telemetry(&mut state.modules, &result, elapsed);
                state.throughput.scored += 1;
                current.push((proposal.clone(), result.clone()));
                scored.push((proposal, result.clone()));
                add_event(
                    &mut archive,
                    "candidate_scored",
                    id,
                    0,
                    json!({
                        "result_hash":result.pointer("/provenance/result_hash"),
                        "claim_locks":collect_claim_locks(&result),
                    }),
                    args.jsonl,
                )?;
                state.records.push(row);
            }
            Err(error) => add_event(
                &mut archive,
                "worker_failed",
                id,
                0,
                json!({"error":error.to_string(),"request_index":index}),
                args.jsonl,
            )?,
        }
    }
    let (attempted, valid, scored_count) = (
        state.throughput.attempted,
        state.throughput.valid,
        state.throughput.scored,
    );
    progress(
        &mut state,
        format!(
            "generation 0/{} complete: attempted {} | valid {} | scored {}",
            args.generations, attempted, valid, scored_count
        ),
    );
    let initial_values: Vec<_> = scored.iter().map(|(_, result)| result.clone()).collect();
    state.candidates = rank_candidates(&initial_values, &profile);
    apply_rank_deltas(&mut state.candidates, None);
    sync_records(&mut state);
    state.objective_ready = state.candidates.iter().any(|candidate| candidate.ranked);
    state.throughput.survivors = state.throughput.survivors.max(
        state
            .candidates
            .iter()
            .filter(|candidate| candidate.feasible)
            .count() as u64,
    );
    state.throughput.solutions = state.throughput.solutions.max(
        state
            .candidates
            .iter()
            .filter(|candidate| candidate.ranked && candidate.feasible)
            .count() as u64,
    );
    state
        .history
        .push(make_score_history(0, &state.candidates, 10));
    state.phase = "RANKED".into();
    add_event(
        &mut archive,
        "candidate_ranked",
        None,
        0,
        json!({"top_10":state.candidates.iter().take(10).collect::<Vec<_>>()}),
        args.jsonl,
    )?;
    archive.snapshot(archive.sequence(), &state)?;
    publish(&sender, &state);
    if cancel.load(Ordering::SeqCst) {
        return Ok(());
    }
    let mut generation = 0;
    for next_generation in 1..=args.generations {
        if cancel.load(Ordering::SeqCst) {
            return Ok(());
        }
        generation = next_generation;
        state.generation = generation;
        state.phase = "PROPOSING".into();
        state.scoring_completed = 0;
        state.scoring_total = 0;
        publish(&sender, &state);
        progress(
            &mut state,
            format!(
                "generation {}/{}: proposing {} mutations",
                generation,
                args.generations,
                args.population.max(1)
            ),
        );
        let ranked_now = rank_candidates(
            &scored
                .iter()
                .map(|(_, result)| result.clone())
                .collect::<Vec<_>>(),
            &profile,
        );
        let parents: Vec<_> = ranked_now
            .iter()
            .take(args.population.max(1))
            .filter_map(|rank| {
                current
                    .iter()
                    .find(|(_, result)| {
                        result
                            .pointer("/candidate/candidate_id")
                            .and_then(Value::as_str)
                            == Some(rank.candidate_id.as_str())
                    })
                    .map(|(candidate, _)| candidate.clone())
            })
            .collect();
        let parents = if parents.is_empty() {
            current
                .iter()
                .map(|(candidate, _)| candidate.clone())
                .collect()
        } else {
            parents
        };
        let mut generation_proposals: Vec<(Value, String)> = Vec::new();
        for index in 0..args.population.max(1) {
            let parent = &parents[index % parents.len()];
            let parent_id = parent
                .get("candidate_id")
                .and_then(Value::as_str)
                .unwrap_or("parent");
            let result = pool.mutate(
                parent,
                args.seed + (generation as u64 * 10_000) + index as u64,
                json!({"parent_ids":[parent_id],"generation":generation,"mutation_id":null}),
            );
            state.throughput.sample(1, 0, 0, 0, 0);
            match result {
                Ok(candidate) => {
                    let id = candidate
                        .get("candidate_id")
                        .and_then(Value::as_str)
                        .map(str::to_string);
                    add_event(
                        &mut archive,
                        "candidate_proposed",
                        id.clone(),
                        generation,
                        json!({"parent_id":parent_id}),
                        args.jsonl,
                    )?;
                    state.throughput.valid += 1;
                    generation_proposals.push((candidate, parent_id.into()));
                }
                Err(error) => {
                    state.rejected_candidates += 1;
                    add_event(
                        &mut archive,
                        "candidate_rejected",
                        Some(parent_id.into()),
                        generation,
                        json!({"reason":error.to_string()}),
                        args.jsonl,
                    )?;
                    publish(&sender, &state);
                }
            }
        }
        let generation_requests: Vec<_> = generation_proposals
            .iter()
            .enumerate()
            .map(|(index, (candidate, _))| {
                (
                    candidate.clone(),
                    args.seed + (generation as u64 * 10_000) + index as u64,
                    lineage(
                        candidate,
                        generation,
                        candidate
                            .pointer("/lineage/mutation_id")
                            .and_then(Value::as_str),
                    ),
                    scoring_run_id.clone(),
                )
            })
            .collect();
        progress(
            &mut state,
            format!(
                "generation {}/{}: {} valid proposals; scoring with {} workers",
                generation,
                args.generations,
                generation_requests.len(),
                args.workers.max(1)
            ),
        );
        let generation_results = score_batch(
            &pool,
            generation_requests,
            "SCORING_GENERATION",
            &mut state,
            &sender,
        )?;
        let mut offspring = Vec::new();
        for ((candidate, _parent_id), scored_result) in
            generation_proposals.into_iter().zip(generation_results)
        {
            let id = candidate
                .get("candidate_id")
                .and_then(Value::as_str)
                .map(str::to_string);
            match scored_result {
                Ok((result, elapsed)) => {
                    envelope_telemetry(&mut state.modules, &result, elapsed);
                    state.throughput.scored += 1;
                    add_event(
                        &mut archive,
                        "candidate_scored",
                        id.clone(),
                        generation,
                        json!({
                            "result_hash":result.pointer("/provenance/result_hash"),
                            "claim_locks":collect_claim_locks(&result),
                        }),
                        args.jsonl,
                    )?;
                    state.records.push(record_from(
                        &candidate,
                        &result,
                        generation,
                        CandidateStatus::Scored,
                    ));
                    scored.push((candidate.clone(), result.clone()));
                    offspring.push((candidate, result));
                }
                Err(error) => add_event(
                    &mut archive,
                    "worker_failed",
                    id,
                    generation,
                    json!({"error":error.to_string()}),
                    args.jsonl,
                )?,
            }
        }
        current = offspring;
        let result_values: Vec<_> = scored.iter().map(|(_, result)| result.clone()).collect();
        let previous_candidates = state.candidates.clone();
        state.candidates = rank_candidates(&result_values, &profile);
        apply_rank_deltas(&mut state.candidates, Some(&previous_candidates));
        sync_records(&mut state);
        state.objective_ready = state.candidates.iter().any(|candidate| candidate.ranked);
        state.throughput.survivors = state.throughput.survivors.max(
            state
                .candidates
                .iter()
                .filter(|candidate| candidate.feasible)
                .count() as u64,
        );
        state.throughput.solutions = state.throughput.solutions.max(
            state
                .candidates
                .iter()
                .filter(|candidate| candidate.ranked && candidate.feasible)
                .count() as u64,
        );
        state
            .history
            .push(make_score_history(generation, &state.candidates, 10));
        state.phase = "RANKED".into();
        add_event(
            &mut archive,
            "candidate_ranked",
            None,
            generation,
            json!({"top_10":state.candidates.iter().take(10).collect::<Vec<_>>()}),
            args.jsonl,
        )?;
        let (attempted, valid, scored_count, survivors, solutions) = (
            state.throughput.attempted,
            state.throughput.valid,
            state.throughput.scored,
            state.throughput.survivors,
            state.throughput.solutions,
        );
        progress(&mut state, format!(
            "generation {}/{} complete: attempted {} | valid {} | scored {} | survivors {} | solutions {}",
            generation, args.generations, attempted, valid, scored_count, survivors, solutions
        ));
        add_event(
            &mut archive,
            "generation_completed",
            None,
            generation,
            json!({"generation":generation,"survivors":state.throughput.survivors,"solutions":state.throughput.solutions}),
            args.jsonl,
        )?;
        archive.snapshot(archive.sequence(), &state)?;
        publish(&sender, &state);
        if args.refresh_ms > 0 {
            for _ in 0..args.refresh_ms.min(1000) {
                if cancel.load(Ordering::SeqCst) {
                    return Ok(());
                }
                std::thread::sleep(std::time::Duration::from_millis(1));
            }
        }
    }
    if state.candidates.is_empty() {
        state.candidates = rank_candidates(
            &scored
                .iter()
                .map(|(_, result)| result.clone())
                .collect::<Vec<_>>(),
            &profile,
        );
    }
    sync_records(&mut state);
    state.objective_ready = state.candidates.iter().any(|candidate| candidate.ranked);
    state.throughput.survivors = state.throughput.survivors.max(
        state
            .candidates
            .iter()
            .filter(|candidate| candidate.feasible)
            .count() as u64,
    );
    state.throughput.solutions = state.throughput.solutions.max(
        state
            .candidates
            .iter()
            .filter(|candidate| candidate.ranked && candidate.feasible)
            .count() as u64,
    );
    state.generation = generation;
    state.phase = "COMPLETE".into();
    state.finished = true;
    add_event(
        &mut archive,
        "run_finished",
        None,
        generation,
        json!({"result_hashes":scored.iter().filter_map(|(_, result)| result.pointer("/provenance/result_hash")).collect::<Vec<_>>()}),
        args.jsonl,
    )?;
    archive.snapshot(archive.sequence(), &state)?;
    archive.final_state(&state)?;
    publish(&sender, &state);
    if args.jsonl {
        println!("{}", serde_json::to_string(&state)?);
    } else if args.headless || !io::stdout().is_terminal() {
        print!("{}", state_text(&state.dashboard()));
    }
    Ok(())
}

fn replay(path: &Path, verify: bool) -> Result<()> {
    let events = amphora_core::read_events(path.join("events.jsonl"))?;
    if verify {
        let root = amphora_core::verify_run(path)?;
        println!("replay verified: {} events root={root}", events.len());
    } else {
        println!("replay checked: {} events", events.len());
    }
    if let Some(last) = events.last() {
        println!(
            "run={} generation={} event={} sequence={}",
            last.run_id, last.generation, last.event_type, last.sequence
        );
    }
    Ok(())
}

fn latest_completed_run(root: &Path) -> Result<PathBuf> {
    let runs = root.join(".amphora/runs");
    fs::read_dir(&runs)?
        .filter_map(|entry| entry.ok())
        .map(|entry| entry.path())
        .filter(|path| path.join("provenance.json").is_file())
        .filter_map(|path| {
            let modified = fs::metadata(path.join("provenance.json"))
                .ok()?
                .modified()
                .ok()?;
            Some((modified, path))
        })
        .max_by_key(|(modified, _)| *modified)
        .map(|(_, path)| path)
        .ok_or_else(|| anyhow!("no completed native run found in {}", runs.display()))
}

fn export(path: &Path, format: ExportFormat) -> Result<()> {
    match format {
        ExportFormat::Json => println!(
            "{}",
            String::from_utf8(fs::read(path.join("final-state.json"))?)?
        ),
        ExportFormat::Jsonl => print!(
            "{}",
            String::from_utf8(fs::read(path.join("events.jsonl"))?)?
        ),
    }
    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let root = workspace_root();
    match cli.command {
        Command::Compound(args) => compound::run(&root, args),
        Command::Data(args) => control::run_data(&root, args),
        Command::Benchmark(args) => control::run_benchmark(&root, args),
        Command::Portfolio(args) => control::run_portfolio(&root, args),
        Command::Shadow(args) => control::run_shadow(&root, args),
        Command::PotLife(args) => control::run_pot_life(&root, args),
        Command::Model(args) => control::run_model(&root, args),
        Command::Demo(args) => run(args, &root, true),
        Command::Run(args) => run(args, &root, false),
        Command::Inspect(args) => run(
            RunArgs {
                candidate: Some(args.candidate),
                population: 1,
                generations: 0,
                workers: 1,
                seed: 42,
                refresh_ms: 0,
                objective_profile: None,
                lane: args.lane,
                headless: args.headless,
                jsonl: args.headless,
            },
            &root,
            false,
        ),
        Command::Replay(args) => {
            let run = match args.run {
                Some(path) => path,
                None => latest_completed_run(&root)?,
            };
            replay(&run, args.verify)
        }
        Command::Resume { run } => {
            replay(&run, true)?;
            println!(
                "resume state is available in {}",
                run.join("final-state.json").display()
            );
            Ok(())
        }
        Command::Export { run, format } => export(&run, format),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn profile_injection_includes_objectives_and_hard_constraints() {
        let profile: KpiProfile = serde_json::from_value(json!({
            "schema":"x", "profile_id":"x",
            "objectives":[{"id":"novelty_score","module_id":"amphora-molecule-novelty","section":"objective_values","path":"novelty_score","label":"Novelty — design-space objective","direction":"maximize","unit":"normalized_0_1","weight":0.30,"display_lower":0.0,"display_upper":1.0}],
            "hard_constraints":[{"id":"gate","module_id":"amphora-molecule-design-gate","section":"gates","path":"pass_all_hard","label":"Design gate","operator":"==","expected":true}],
            "display_kpis":[]
        })).unwrap();
        let candidate = inject_profile(json!({"candidate_id":"x","context":{}}), &profile);
        assert_eq!(
            candidate.pointer("/context/optimization_request/objective_list/0/path"),
            Some(&Value::String("novelty_score".into()))
        );
        assert_eq!(
            candidate.pointer("/context/optimization_request/hard_constraints/0/expected"),
            Some(&Value::Bool(true))
        );
    }

    #[test]
    fn fixed_demo_configuration_has_a_stable_run_identity() {
        let candidate = json!({"candidate_id":"μ-demo","candidate_type":"molecule"});
        let first = deterministic_run_id(&candidate, 42, 25, 2, 2, "molecule", "molecule-demo-v1");
        let second = deterministic_run_id(&candidate, 42, 25, 2, 2, "molecule", "molecule-demo-v1");
        assert_eq!(first, second);
        assert_ne!(
            first,
            deterministic_run_id(&candidate, 43, 25, 2, 2, "molecule", "molecule-demo-v1")
        );
    }

    #[test]
    fn live_profile_without_design_gate_fails_closed() {
        let path = std::env::temp_dir().join(format!(
            "amphora-profile-without-gate-{}.json",
            std::process::id()
        ));
        fs::write(
            &path,
            serde_json::to_vec(&json!({
                "schema":"x", "profile_id":"unsafe", "objectives":[],
                "hard_constraints":[], "display_kpis":[]
            }))
            .unwrap(),
        )
        .unwrap();
        let error = load_profile(Path::new("."), Some(&path)).unwrap_err();
        let _ = fs::remove_file(path);
        assert!(error
            .to_string()
            .contains("molecule-design-gate.gates.pass_all_hard == true"));
    }

    #[test]
    fn pot_life_protocol_command_is_separate_from_legacy_benchmark_commands() {
        let cli = Cli::try_parse_from([
            "amphora-tui",
            "pot-life",
            "protocol",
            "--qualification",
            "qualification.json",
            "--source-ledger",
            "ledger.json",
            "--generated-on",
            "2026-07-17",
            "--mixing-method",
            "locked-mixer",
        ])
        .unwrap();
        assert!(matches!(
            cli.command,
            Command::PotLife(control::PotLifeArgs {
                command: control::PotLifeCommand::Protocol { .. }
            })
        ));

        let legacy = Cli::try_parse_from([
            "amphora-tui",
            "benchmark",
            "run",
            "--locked",
            "--module",
            "amphora-cure-potlife-gate",
        ])
        .unwrap();
        assert!(matches!(legacy.command, Command::Benchmark(_)));
    }

    #[test]
    fn pot_life_preflight_parses_all_operator_arguments() {
        let cli = Cli::try_parse_from([
            "amphora-tui",
            "pot-life",
            "preflight",
            "--kind",
            "run",
            "--input",
            "run.json",
            "--raw-base-dir",
            "raw",
        ])
        .unwrap();
        assert!(matches!(
            cli.command,
            Command::PotLife(control::PotLifeArgs {
                command: control::PotLifeCommand::Preflight { .. }
            })
        ));
    }

    #[test]
    fn scientific_model_preflight_and_fit_parse_exact_workflow() {
        let preflight = Cli::try_parse_from([
            "amphora-tui",
            "model",
            "preflight",
            "--module",
            "amphora-solvency-score",
            "--kind",
            "parameter-artifact",
            "--input",
            "parameters.json",
            "--raw-base-dir",
            "raw",
        ])
        .unwrap();
        assert!(matches!(
            preflight.command,
            Command::Model(control::ModelArgs {
                command: control::ModelCommand::Preflight { .. }
            })
        ));

        let fit = Cli::try_parse_from([
            "amphora-tui",
            "model",
            "fit",
            "--module",
            "amphora-viscosity-score",
            "--dataset",
            "dataset.json",
            "--split",
            "split.json",
            "--lock",
            "lock.json",
            "--output",
            "model.json",
        ])
        .unwrap();
        assert!(matches!(
            fit.command,
            Command::Model(control::ModelArgs {
                command: control::ModelCommand::Fit { .. }
            })
        ));
    }
}
