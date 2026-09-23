//! Deterministic NSGA-II (Deb et al. 2002) for minimization with
//! constrained-dominance. Determinism by construction: pinned splitmix64
//! seed, deterministic binary tournament with index tie-breaks, stable sorts
//! with explicit total orders, ordered reductions in crowding distances.
//! No external RNG crate: splitmix64 is bit-exact on every platform.

use std::cmp::Ordering;

/// splitmix64 (Steele/Lea/Flood 2014) - tiny, seedable, bit-exact.
pub struct SplitMix64 {
    s: u64,
}

impl SplitMix64 {
    pub fn new(seed: u64) -> Self {
        Self { s: seed }
    }

    pub fn next_u64(&mut self) -> u64 {
        self.s = self.s.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.s;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }

    /// Uniform in [0, 1) with 53-bit resolution.
    pub fn next_f64(&mut self) -> f64 {
        (self.next_u64() >> 11) as f64 * (1.0 / 9_007_199_254_740_992.0)
    }

    pub fn next_usize_below(&mut self, n: usize) -> usize {
        assert!(n > 0);
        (self.next_u64() % (n as u64)) as usize
    }
}

#[derive(Clone, Debug, PartialEq)]
pub struct Individual {
    pub genes: Vec<f64>,
    pub objectives: Vec<f64>,
    /// Total constraint violation; 0.0 means feasible.
    pub cv: f64,
}

#[derive(Clone, Debug)]
pub struct Nsga2Config {
    pub pop_size: usize,
    pub generations: usize,
    pub seed: u64,
    pub eta_crossover: f64,
    pub eta_mutation: f64,
    pub p_crossover: f64,
    pub p_mutation: f64,
    pub gene_lo: f64,
    pub gene_hi: f64,
}

fn clamp(x: f64, lo: f64, hi: f64) -> f64 {
    x.max(lo).min(hi)
}

/// Deb's constrained-dominance: feasible beats infeasible; among infeasible,
/// lower violation wins; among feasible, Pareto dominance (minimization).
pub fn constrained_dominates(a: &Individual, b: &Individual) -> bool {
    let af = a.cv <= 0.0;
    let bf = b.cv <= 0.0;
    if af && !bf {
        return true;
    }
    if !af && bf {
        return false;
    }
    if !af && !bf {
        return a.cv < b.cv;
    }
    let mut strictly_better = false;
    for (x, y) in a.objectives.iter().zip(b.objectives.iter()) {
        if x > y {
            return false;
        }
        if x < y {
            strictly_better = true;
        }
    }
    strictly_better
}

/// Fast non-dominated sort; returns rank per individual (0 = best front).
fn ranks(pop: &[Individual]) -> Vec<usize> {
    let n = pop.len();
    let mut dominated_count = vec![0usize; n];
    let mut dominates_list: Vec<Vec<usize>> = vec![Vec::new(); n];
    for i in 0..n {
        for j in 0..n {
            if i != j && constrained_dominates(&pop[i], &pop[j]) {
                dominates_list[i].push(j);
                dominated_count[j] += 1;
            }
        }
    }
    let mut rank = vec![usize::MAX; n];
    let mut current: Vec<usize> = (0..n).filter(|&i| dominated_count[i] == 0).collect();
    let mut r = 0usize;
    while !current.is_empty() {
        for &i in &current {
            rank[i] = r;
        }
        let mut next: Vec<usize> = Vec::new();
        for &i in &current {
            for &j in &dominates_list[i] {
                dominated_count[j] -= 1;
                if dominated_count[j] == 0 {
                    next.push(j);
                }
            }
        }
        next.sort_unstable();
        current = next;
        r += 1;
    }
    rank
}

/// Crowding distance for the index set `front` (all same rank), aligned with
/// `front` order. Ordered reductions: per-objective stable sort with index
/// tie-break, then sequential accumulation.
fn crowding_for_front(pop: &[Individual], front: &[usize]) -> Vec<f64> {
    let len = front.len();
    let mut dist = vec![0.0_f64; len];
    if len == 0 {
        return dist;
    }
    let m = pop[front[0]].objectives.len();
    for k in 0..m {
        let mut order: Vec<usize> = (0..len).collect();
        order.sort_by(|&a, &b| {
            pop[front[a]].objectives[k]
                .partial_cmp(&pop[front[b]].objectives[k])
                .expect("finite objectives")
                .then(front[a].cmp(&front[b]))
        });
        let first = order[0];
        let last = *order.last().expect("non-empty front");
        let fmin = pop[front[first]].objectives[k];
        let fmax = pop[front[last]].objectives[k];
        dist[first] = f64::INFINITY;
        dist[last] = f64::INFINITY;
        if fmax > fmin && len > 2 {
            for w in 1..len - 1 {
                let idx = order[w];
                if dist[idx].is_finite() {
                    let lo = pop[front[order[w - 1]]].objectives[k];
                    let hi = pop[front[order[w + 1]]].objectives[k];
                    dist[idx] += (hi - lo) / (fmax - fmin);
                }
            }
        }
    }
    dist
}

/// Crowding distances aligned with the whole population.
fn crowding_all(pop: &[Individual], rank: &[usize]) -> Vec<f64> {
    let n = pop.len();
    let mut crowd = vec![0.0_f64; n];
    let max_rank = rank.iter().copied().max().unwrap_or(0);
    for r in 0..=max_rank {
        let front: Vec<usize> = (0..n).filter(|&i| rank[i] == r).collect();
        let d = crowding_for_front(pop, &front);
        for (slot, &i) in front.iter().enumerate() {
            crowd[i] = d[slot];
        }
    }
    crowd
}

/// Deterministic binary tournament: rank, then crowding, then lowest index.
fn tournament(rng: &mut SplitMix64, rank: &[usize], crowd: &[f64], n: usize) -> usize {
    let a = rng.next_usize_below(n);
    let b = rng.next_usize_below(n);
    if rank[a] < rank[b] {
        a
    } else if rank[b] < rank[a] {
        b
    } else if crowd[a] > crowd[b] {
        a
    } else if crowd[b] > crowd[a] {
        b
    } else {
        a.min(b)
    }
}

fn sbx_crossover(
    rng: &mut SplitMix64,
    p1: &[f64],
    p2: &[f64],
    cfg: &Nsga2Config,
) -> (Vec<f64>, Vec<f64>) {
    let mut c1 = p1.to_vec();
    let mut c2 = p2.to_vec();
    if rng.next_f64() <= cfg.p_crossover {
        for i in 0..p1.len() {
            if rng.next_f64() <= 0.5 {
                let u = rng.next_f64();
                let exponent = 1.0 / (cfg.eta_crossover + 1.0);
                let beta = if u <= 0.5 {
                    (2.0 * u).powf(exponent)
                } else {
                    (1.0 / (2.0 * (1.0 - u))).powf(exponent)
                };
                let (x1, x2) = (p1[i], p2[i]);
                c1[i] = clamp(0.5 * ((1.0 + beta) * x1 + (1.0 - beta) * x2), cfg.gene_lo, cfg.gene_hi);
                c2[i] = clamp(0.5 * ((1.0 - beta) * x1 + (1.0 + beta) * x2), cfg.gene_lo, cfg.gene_hi);
            }
        }
    }
    (c1, c2)
}

fn polynomial_mutation(rng: &mut SplitMix64, genes: &mut [f64], cfg: &Nsga2Config) {
    let span = cfg.gene_hi - cfg.gene_lo;
    for g in genes.iter_mut() {
        if rng.next_f64() <= cfg.p_mutation {
            let u = rng.next_f64();
            let exponent = 1.0 / (cfg.eta_mutation + 1.0);
            let delta = if u < 0.5 {
                (2.0 * u).powf(exponent) - 1.0
            } else {
                1.0 - (2.0 * (1.0 - u)).powf(exponent)
            };
            *g = clamp(*g + delta * span, cfg.gene_lo, cfg.gene_hi);
        }
    }
}

fn lex_cmp(a: &[f64], b: &[f64]) -> Ordering {
    for (x, y) in a.iter().zip(b.iter()) {
        match x.partial_cmp(y).expect("finite") {
            Ordering::Equal => continue,
            o => return o,
        }
    }
    a.len().cmp(&b.len())
}

/// Run NSGA-II; `eval(genes) -> (objectives_to_minimize, constraint_violation)`.
/// `seed_genes` are deterministic starting individuals (e.g. known vertices)
/// injected at the head of the initial population; the rest is drawn from the
/// pinned PRNG. Returns the final feasible rank-0 front, deduplicated and
/// sorted lexicographically by objectives then genes (deterministic
/// presentation).
pub fn run<E>(cfg: &Nsga2Config, n_genes: usize, seed_genes: &[Vec<f64>], eval: E) -> Vec<Individual>
where
    E: Fn(&[f64]) -> (Vec<f64>, f64),
{
    assert!(cfg.pop_size >= 4 && cfg.pop_size % 2 == 0);
    assert!(seed_genes.len() <= cfg.pop_size);
    let mk = |genes: Vec<f64>, eval: &E| -> Individual {
        let (objectives, cv) = eval(&genes);
        for o in &objectives {
            assert!(o.is_finite(), "objectives must be finite");
        }
        assert!(cv.is_finite() && cv >= 0.0, "cv must be finite and >= 0");
        Individual { genes, objectives, cv }
    };

    let mut rng = SplitMix64::new(cfg.seed);
    let mut pop: Vec<Individual> = Vec::with_capacity(cfg.pop_size);
    for s in seed_genes {
        assert_eq!(s.len(), n_genes);
        let genes: Vec<f64> = s.iter().map(|&g| clamp(g, cfg.gene_lo, cfg.gene_hi)).collect();
        pop.push(mk(genes, &eval));
    }
    while pop.len() < cfg.pop_size {
        let genes: Vec<f64> = (0..n_genes)
            .map(|_| cfg.gene_lo + (cfg.gene_hi - cfg.gene_lo) * rng.next_f64())
            .collect();
        pop.push(mk(genes, &eval));
    }

    for _gen in 0..cfg.generations {
        let rank = ranks(&pop);
        let crowd = crowding_all(&pop, &rank);

        let mut children: Vec<Individual> = Vec::with_capacity(cfg.pop_size);
        while children.len() < cfg.pop_size {
            let ia = tournament(&mut rng, &rank, &crowd, pop.len());
            let ib = tournament(&mut rng, &rank, &crowd, pop.len());
            let (mut c1, mut c2) = sbx_crossover(&mut rng, &pop[ia].genes, &pop[ib].genes, cfg);
            polynomial_mutation(&mut rng, &mut c1, cfg);
            polynomial_mutation(&mut rng, &mut c2, cfg);
            children.push(mk(c1, &eval));
            if children.len() < cfg.pop_size {
                children.push(mk(c2, &eval));
            }
        }

        let mut combined = pop;
        combined.extend(children);
        let crank = ranks(&combined);
        let ccrowd = crowding_all(&combined, &crank);
        let mut order: Vec<usize> = (0..combined.len()).collect();
        order.sort_by(|&a, &b| {
            crank[a]
                .cmp(&crank[b])
                .then_with(|| ccrowd[b].partial_cmp(&ccrowd[a]).expect("crowding comparable"))
                .then(a.cmp(&b))
        });
        pop = order[..cfg.pop_size]
            .iter()
            .map(|&i| combined[i].clone())
            .collect();
    }

    let rank = ranks(&pop);
    let mut front: Vec<Individual> = pop
        .into_iter()
        .zip(rank)
        .filter(|(ind, r)| *r == 0 && ind.cv <= 0.0)
        .map(|(ind, _)| ind)
        .collect();
    front.sort_by(|a, b| lex_cmp(&a.objectives, &b.objectives).then_with(|| lex_cmp(&a.genes, &b.genes)));
    front.dedup_by(|a, b| a.objectives == b.objectives && a.genes == b.genes);
    front
}
