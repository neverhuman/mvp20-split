//! Exhaustive DoE enumeration: canonical Cartesian cell enumeration over
//! named axes. Canonical order: axes sorted by name (byte order), cells in
//! mixed-radix order with the LAST (sorted) axis varying fastest. This is a
//! declarative accounting enumeration - it makes no feasibility claims.

#[derive(Clone, Debug)]
pub struct Axis {
    pub name: String,
    pub levels: Vec<String>,
}

/// Enumerate every cell of the full-factorial universe in canonical order.
/// Each cell is a Vec of (axis_name, level) in sorted-axis order.
pub fn enumerate_cells(axes: &[Axis]) -> Vec<Vec<(String, String)>> {
    assert!(!axes.is_empty());
    let mut sorted: Vec<Axis> = axes.to_vec();
    sorted.sort_by(|a, b| a.name.cmp(&b.name));
    for ax in &sorted {
        assert!(!ax.levels.is_empty(), "axis {} has no levels", ax.name);
    }
    let total: usize = sorted.iter().map(|a| a.levels.len()).product();
    let mut out = Vec::with_capacity(total);
    for cell_index in 0..total {
        let mut idx = cell_index;
        let mut cell = vec![(String::new(), String::new()); sorted.len()];
        for (k, ax) in sorted.iter().enumerate().rev() {
            let m = ax.levels.len();
            cell[k] = (ax.name.clone(), ax.levels[idx % m].clone());
            idx /= m;
        }
        out.push(cell);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_order_2x2() {
        let axes = vec![
            Axis {
                name: "b_axis".into(),
                levels: vec!["x".into(), "y".into()],
            },
            Axis {
                name: "a_axis".into(),
                levels: vec!["1".into(), "2".into()],
            },
        ];
        let cells = enumerate_cells(&axes);
        assert_eq!(cells.len(), 4);
        // Axes sorted: a_axis first; last axis (b_axis) fastest.
        assert_eq!(
            cells[0],
            vec![("a_axis".to_string(), "1".to_string()), ("b_axis".to_string(), "x".to_string())]
        );
        assert_eq!(
            cells[1],
            vec![("a_axis".to_string(), "1".to_string()), ("b_axis".to_string(), "y".to_string())]
        );
        assert_eq!(
            cells[2],
            vec![("a_axis".to_string(), "2".to_string()), ("b_axis".to_string(), "x".to_string())]
        );
        assert_eq!(
            cells[3],
            vec![("a_axis".to_string(), "2".to_string()), ("b_axis".to_string(), "y".to_string())]
        );
    }

    #[test]
    fn cardinality_2e4() {
        let axes: Vec<Axis> = (0..4)
            .map(|i| Axis {
                name: format!("f{}", i),
                levels: vec!["lo".into(), "hi".into()],
            })
            .collect();
        assert_eq!(enumerate_cells(&axes).len(), 16);
    }
}
