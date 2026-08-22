use amphora_solver_lab::nsga2::{run, Nsga2Config};

fn cfg(seed: u64) -> Nsga2Config {
    Nsga2Config {
        pop_size: 32,
        generations: 40,
        seed,
        eta_crossover: 15.0,
        eta_mutation: 20.0,
        p_crossover: 0.9,
        p_mutation: 1.0 / 3.0,
        gene_lo: 0.0,
        gene_hi: 1.0,
    }
}

/// Small constrained bi-objective problem (ZDT1-flavoured with a cap).
fn eval(genes: &[f64]) -> (Vec<f64>, f64) {
    let f1 = genes[0];
    let g = 1.0 + 9.0 * (genes[1] + genes[2]) / 2.0;
    let f2 = g * (1.0 - (f1 / g).sqrt());
    let cv = (f1 + f2 - 1.5).max(0.0); // constraint: f1 + f2 <= 1.5
    (vec![f1, f2], cv)
}

fn serialize_front(front: &[amphora_solver_lab::nsga2::Individual]) -> String {
    let rows: Vec<serde_json::Value> = front
        .iter()
        .map(|ind| {
            serde_json::json!({
                "genes": ind.genes,
                "objectives": ind.objectives,
                "cv": ind.cv,
            })
        })
        .collect();
    serde_json::to_string(&rows).expect("serializable")
}

#[test]
fn two_runs_same_seed_are_bit_identical() {
    let a = run(&cfg(0xA11CE), 3, &[], eval);
    let b = run(&cfg(0xA11CE), 3, &[], eval);
    assert!(!a.is_empty(), "front must not be empty");
    assert_eq!(
        serialize_front(&a),
        serialize_front(&b),
        "two NSGA-II runs with the same pinned seed must be bit-identical"
    );
}

#[test]
fn front_is_feasible_and_mutually_nondominated() {
    let front = run(&cfg(7), 3, &[], eval);
    assert!(!front.is_empty());
    for ind in &front {
        assert_eq!(ind.cv, 0.0, "front members must be exactly feasible");
    }
    for a in &front {
        for b in &front {
            if a.genes != b.genes {
                assert!(
                    !amphora_solver_lab::nsga2::constrained_dominates(a, b)
                        || !amphora_solver_lab::nsga2::constrained_dominates(b, a),
                    "mutual domination is impossible"
                );
            }
        }
    }
}

#[test]
fn seeded_individuals_enter_generation_zero() {
    // A seeded feasible vertex must survive into a nonempty feasible front
    // even with zero generations of evolution.
    let mut c = cfg(3);
    c.generations = 0;
    let seeds = vec![vec![0.1, 0.0, 0.0]];
    let front = run(&c, 3, &seeds, eval);
    assert!(
        front.iter().any(|ind| ind.genes == vec![0.1, 0.0, 0.0]),
        "seeded genes must be present in the generation-0 population"
    );
}
