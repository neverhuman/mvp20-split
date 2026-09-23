use amphora_solver_lab::simplex::project_to_simplex;

fn assert_close(a: f64, b: f64) {
    assert!((a - b).abs() < 1e-12, "{a} != {b}");
}

#[test]
fn known_answer_vertex() {
    let x = project_to_simplex(&[2.0, 0.0, 0.0]);
    assert_eq!(x, vec![1.0, 0.0, 0.0]);
}

#[test]
fn known_answer_uniform_lift() {
    // [0.3, 0.3, 0.3] sums to 0.9; projection adds 0.1/3 to each coordinate.
    let x = project_to_simplex(&[0.3, 0.3, 0.3]);
    for xi in &x {
        assert_close(*xi, 1.0 / 3.0);
    }
}

#[test]
fn known_answer_clips_negative() {
    let x = project_to_simplex(&[1.2, -0.2]);
    assert_eq!(x, vec![1.0, 0.0]);
}

#[test]
fn projection_is_idempotent_on_simplex_points() {
    for p in [
        vec![1.0, 0.0, 0.0, 0.0],
        vec![0.25, 0.25, 0.25, 0.25],
        vec![0.5, 0.5],
        vec![0.7, 0.2, 0.1],
    ] {
        let x = project_to_simplex(&p);
        for (a, b) in x.iter().zip(p.iter()) {
            assert_close(*a, *b);
        }
    }
}

#[test]
fn output_is_always_on_simplex() {
    let inputs = [
        vec![10.0, -3.0, 0.5, 0.0, 2.0],
        vec![-1.0, -2.0, -3.0],
        vec![0.0, 0.0],
        vec![1e6, 1e-6],
        vec![0.123456789, 0.987654321, 0.5, 0.25, 0.125, 0.0625],
    ];
    for v in &inputs {
        let x = project_to_simplex(v);
        let mut sum = 0.0;
        for xi in &x {
            assert!(*xi >= 0.0, "negative coordinate {xi}");
            sum += xi;
        }
        assert!((sum - 1.0).abs() < 1e-9, "sum {sum} != 1 for input {v:?}");
    }
}

#[test]
fn projection_is_deterministic() {
    let v = vec![0.9, 0.1, 0.4, -0.2, 0.35, 0.05];
    let a = project_to_simplex(&v);
    let b = project_to_simplex(&v);
    assert_eq!(a, b, "two projections of the same input must be bit-identical");
}
