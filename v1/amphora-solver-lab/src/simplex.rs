//! Deterministic Euclidean projection onto the probability simplex
//! {x : x_i >= 0, sum x_i = 1} (sort-based algorithm; Held/Wolfe/Crowder 1974,
//! Duchi et al. 2008) and a projected-gradient minimizer over the simplex.
//! f64 only; descending sort with a total order on finite inputs; ordered
//! cumulative sums.

/// Project v onto the probability simplex. Panics on empty or non-finite
/// input (inputs are always finite by construction in this crate).
pub fn project_to_simplex(v: &[f64]) -> Vec<f64> {
    assert!(!v.is_empty(), "cannot project an empty vector");
    for x in v {
        assert!(x.is_finite(), "simplex projection requires finite inputs");
    }
    let mut u = v.to_vec();
    // Descending, deterministic: finite f64 partial_cmp is a total order here.
    u.sort_by(|a, b| b.partial_cmp(a).expect("finite"));
    let mut cum = 0.0_f64; // ordered cumulative sum
    let mut tau = f64::NAN;
    let mut found = false;
    for (i, ui) in u.iter().enumerate() {
        cum += ui;
        let t = (cum - 1.0) / ((i + 1) as f64);
        if ui - t > 0.0 {
            tau = t;
            found = true;
        }
    }
    assert!(found, "simplex projection support set is never empty");
    v.iter().map(|&x| (x - tau).max(0.0)).collect()
}

/// Deterministic projected gradient descent over the probability simplex:
/// fixed step, fixed iteration count, no line search, no randomness.
pub fn projected_gradient_min<F, G>(
    x0: &[f64],
    f: F,
    grad: G,
    step: f64,
    iters: usize,
) -> (Vec<f64>, f64)
where
    F: Fn(&[f64]) -> f64,
    G: Fn(&[f64]) -> Vec<f64>,
{
    let mut x = project_to_simplex(x0);
    for _ in 0..iters {
        let g = grad(&x);
        assert_eq!(g.len(), x.len());
        let y: Vec<f64> = x.iter().zip(g.iter()).map(|(xi, gi)| xi - step * gi).collect();
        x = project_to_simplex(&y);
    }
    let fx = f(&x);
    (x, fx)
}
