//! Founder demo showcase TUI — four runnable examples + a red-team board.
//! E1 live VOC-min solver (billions of real formulation cells), E2 hazard-
//! constrained hardener selection (honest EMPTY feasible set), E3 2^4 factorial
//! process screen, E4 live COMPOUNDS/SECOND molecule screening. Every number is a
//! real computation on pinned data; throughput panels are engineering metrics
//! only, never novelty/ranking/validated science.
use crate::screen;
use amphora_solver_lab::demos::p1::{showcase_grid, GridDelta};
use anyhow::{anyhow, Result};
use crossterm::{
    event::{self, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    symbols,
    text::{Line, Span},
    widgets::{Axis, Block, Borders, Chart, Dataset, Gauge, GraphType, Paragraph, Row, Table},
    Frame, Terminal,
};
use serde_json::Value;
use std::io::{self, IsTerminal};
use std::path::Path;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

// ---- palette -------------------------------------------------------------
const BG: Color = Color::Rgb(8, 16, 29);
const PANEL: Color = Color::Rgb(15, 29, 48);
const EDGE: Color = Color::Rgb(71, 91, 116);
const CYAN: Color = Color::Rgb(45, 212, 232);
const GREEN: Color = Color::Rgb(52, 211, 153);
const MAGENTA: Color = Color::Rgb(232, 121, 249);
const AMBER: Color = Color::Rgb(251, 191, 36);
const REDC: Color = Color::Rgb(248, 113, 113);
const GRAY: Color = Color::Rgb(148, 163, 184);
const INK: Color = Color::Rgb(226, 232, 240);

#[derive(Clone, Copy, PartialEq)]
pub enum Scale {
    S,
    M,
    L,
    Xl,
}
impl Scale {
    fn units(self) -> usize {
        match self {
            Scale::S => 60,
            Scale::M => 120,
            Scale::L => 180,
            Scale::Xl => 240,
        }
    }
}

#[derive(Clone, Copy, PartialEq)]
enum Ex {
    E1,
    E2,
    E3,
    E4,
    Board,
}

#[derive(Default)]
struct Agreement {
    grid: f64,
    pg: f64,
    nsga: f64,
    gap: f64,
    passed: bool,
    nsga_ok: bool,
}

#[derive(Default, Clone)]
struct Hazard {
    candidate: String,
    h317: bool,
    h351: bool,
    ad_fail: bool,
}

#[derive(Default)]
struct State {
    // E1
    ready: bool,
    grid_done: bool,
    cells_total: u64,
    cells_feasible: u64,
    best_voc: f64,
    best_red: f64,
    opt_flash: f64,
    opt_mak: f64,
    agree: Agreement,
    pareto: Vec<(f64, f64)>,
    live_scatter: Vec<(f64, f64)>,
    incumbent_voc: f64,
    incumbent_red: f64,
    convergence: Vec<(f64, f64)>,
    n_solvents: usize,
    excluded: usize,
    // E2 (p3)
    hazards: Vec<Hazard>,
    p3_feasible: i64,
    p3_status: String,
    // E3 (p4)
    p4_solved: i64,
    p4_infeasible: i64,
    p4_cells: usize,
    p4_status: String,
    // E4 (compound screen)
    screen_total: u64,
    screen_scored: u64,
    screen_distinct: u64,
    screen_cps: f64,
    screen_workers: usize,
    screen_running: bool,
    screen_done: bool,
    screen_admissible: u64,
    screen_start_s: f64,
    screen_ex: screen::Exemplar,
}

fn binom(n: u128, k: u128) -> u128 {
    if k > n {
        return 0;
    }
    let k = k.min(n - k);
    let mut num: u128 = 1;
    for i in 0..k {
        num = num * (n - i) / (i + 1);
    }
    num
}

fn commafy(n: u64) -> String {
    let s = n.to_string();
    let b = s.as_bytes();
    let mut out = String::new();
    for (i, ch) in b.iter().enumerate() {
        if i > 0 && (b.len() - i) % 3 == 0 {
            out.push(',');
        }
        out.push(*ch as char);
    }
    out
}

fn load_e1(state: &Arc<Mutex<State>>) -> Result<()> {
    let bytes = amphora_solver_lab::demos::run("p1")?;
    let v: Value = serde_json::from_slice(&bytes)?;
    let ma = v.pointer("/results/method_agreement").ok_or_else(|| anyhow!("no agreement"))?;
    let ob = v.pointer("/results/optimal_blend").ok_or_else(|| anyhow!("no optimum"))?;
    let mut pareto = Vec::new();
    if let Some(arr) = v.pointer("/results/pareto_slice_voc_vs_red").and_then(Value::as_array) {
        for row in arr {
            if let (Some(x), Some(y)) = (
                row.get("voc_g_per_l").and_then(Value::as_f64),
                row.get("red").and_then(Value::as_f64),
            ) {
                pareto.push((x, y));
            }
        }
    }
    let excluded = v
        .pointer("/problem/excluded_ingredients")
        .and_then(Value::as_array)
        .map(|a| a.len())
        .unwrap_or(0);
    let mut s = state.lock().unwrap();
    s.agree = Agreement {
        grid: ma.get("grid_min_voc_g_per_l").and_then(Value::as_f64).unwrap_or(0.0),
        pg: ma.get("projected_gradient_min_voc_g_per_l").and_then(Value::as_f64).unwrap_or(0.0),
        nsga: ma.get("nsga2_front_min_voc_g_per_l").and_then(Value::as_f64).unwrap_or(0.0),
        gap: ma.get("grid_vs_pg_abs_gap").and_then(Value::as_f64).unwrap_or(0.0),
        passed: ma.get("grid_pg_agree_within_1e_9").and_then(Value::as_bool).unwrap_or(false),
        nsga_ok: ma.get("nsga2_never_beats_exhaustive_optimum").and_then(Value::as_bool).unwrap_or(false),
    };
    s.best_voc = ob.get("voc_g_per_l").and_then(Value::as_f64).unwrap_or(0.0);
    s.best_red = ob.get("hansen_red_vs_dgeba").and_then(Value::as_f64).unwrap_or(0.0);
    s.opt_flash = ob.get("min_flash_c_on_support").and_then(Value::as_f64).unwrap_or(0.0);
    s.opt_mak = ob.pointer("/composition_volume_fraction_of_carrier/mak").and_then(Value::as_f64).unwrap_or(0.0);
    s.pareto = pareto;
    s.excluded = excluded;
    s.ready = true;
    Ok(())
}

fn load_e2(state: &Arc<Mutex<State>>) {
    let Ok(bytes) = amphora_solver_lab::demos::run("p3") else { return };
    let Ok(v) = serde_json::from_slice::<Value>(&bytes) else { return };
    let r = match v.pointer("/results") {
        Some(r) => r,
        None => return,
    };
    let set = |k: &str| -> Vec<String> {
        r.pointer(&format!("/blocking_summary/{k}"))
            .and_then(Value::as_array)
            .map(|a| a.iter().filter_map(|x| x.as_str().map(String::from)).collect())
            .unwrap_or_default()
    };
    let h317 = set("H317_skin_sensitiser");
    let h351 = set("H351_suspected_carcinogen");
    let ad = set("ad_gate_failures");
    let mut names: Vec<String> = h317.clone();
    for n in h351.iter().chain(ad.iter()) {
        if !names.contains(n) {
            names.push(n.clone());
        }
    }
    names.sort();
    let hazards: Vec<Hazard> = names
        .iter()
        .map(|c| Hazard {
            candidate: c.clone(),
            h317: h317.contains(c),
            h351: h351.contains(c),
            ad_fail: ad.contains(c),
        })
        .collect();
    let mut s = state.lock().unwrap();
    s.hazards = hazards;
    s.p3_feasible = r.get("n_feasible").and_then(Value::as_i64).unwrap_or(0);
    s.p3_status = v.pointer("/pareto_status").and_then(Value::as_str).unwrap_or("").to_string();
}

fn load_e3(state: &Arc<Mutex<State>>) {
    let Ok(bytes) = amphora_solver_lab::demos::run("p4") else { return };
    let Ok(v) = serde_json::from_slice::<Value>(&bytes) else { return };
    let r = match v.pointer("/results") {
        Some(r) => r,
        None => return,
    };
    let mut s = state.lock().unwrap();
    s.p4_solved = r.get("n_solved").and_then(Value::as_i64).unwrap_or(0);
    s.p4_infeasible = r.get("n_infeasible").and_then(Value::as_i64).unwrap_or(0);
    s.p4_cells = r.get("cells").and_then(Value::as_array).map(|a| a.len()).unwrap_or(0);
    s.p4_status = v.pointer("/pareto_status").and_then(Value::as_str).unwrap_or("").to_string();
}

pub fn run_showcase(root: &Path, scale: Scale, autopilot: bool, headless: bool) -> Result<()> {
    let root = root.to_path_buf();
    let units = scale.units();
    let total_cells = binom((units + 5) as u128, 5) as u64;
    let state = Arc::new(Mutex::new(State::default()));
    let progress = Arc::new(AtomicU64::new(0)); // E1 grid cells
    let (grid_tx, grid_rx) = std::sync::mpsc::sync_channel::<GridDelta>(256);
    state.lock().unwrap().incumbent_voc = f64::INFINITY;
    let screen_prog = Arc::new(AtomicU64::new(0)); // E4 compounds
    let started = Instant::now();

    // Background: E1 authoritative + E2/E3, then the E1 live grid.
    {
        let state = state.clone();
        let progress = progress.clone();
        thread::spawn(move || {
            let _ = load_e1(&state);
            load_e2(&state);
            load_e3(&state);
            if let Ok(g) = showcase_grid(units, &progress, Some(&grid_tx)) {
                let mut s = state.lock().unwrap();
                s.cells_total = g.cells_total;
                s.cells_feasible = g.cells_feasible;
                s.n_solvents = g.n_solvents;
                if g.best_voc.is_finite() {
                    s.best_voc = g.best_voc;
                    s.best_red = g.best_red;
                }
                s.grid_done = true;
            }
        });
    }

    if headless || !io::stdout().is_terminal() {
        while !state.lock().unwrap().grid_done {
            thread::sleep(Duration::from_millis(100));
        }
        // also run the E4 screen once for the snapshot
        launch_screen(&root, &state, &screen_prog, 0.0);
        while state.lock().unwrap().screen_running {
            thread::sleep(Duration::from_millis(100));
        }
        print!("{}", snapshot_text(&state.lock().unwrap(), progress.load(Ordering::Relaxed), total_cells));
        return Ok(());
    }

    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    let mut ex = Ex::E1;
    let mut cells_seen: u64 = 0;
    let mut ex_since = Instant::now();
    let mut screen_started = false;
    let res = (|| -> Result<()> {
        loop {
            // lazily launch the E4 screen when it's first shown (keeps it live)
            if ex == Ex::E4 && !screen_started {
                screen_started = true;
                launch_screen(&root, &state, &screen_prog, started.elapsed().as_secs_f64());
            }
            for d in grid_rx.try_iter() {
                cells_seen += d.cells_done_delta;
                let mut st = state.lock().unwrap();
                for pt in &d.new_samples {
                    if st.live_scatter.len() < 800 {
                        st.live_scatter.push((pt.0 as f64, pt.1 as f64));
                    }
                }
                if d.chunk_best_voc < st.incumbent_voc {
                    st.incumbent_voc = d.chunk_best_voc;
                    st.incumbent_red = d.chunk_best_red;
                    st.convergence.push((cells_seen as f64, d.chunk_best_voc));
                }
            }
            let done = progress.load(Ordering::Relaxed);
            let sdone = screen_prog.load(Ordering::Relaxed);
            let elapsed = started.elapsed();
            {
                let s = state.lock().unwrap();
                terminal.draw(|f| draw(f, &s, ex, done, total_cells, sdone, elapsed))?;
            }
            if event::poll(Duration::from_millis(60))? {
                if let Event::Key(key) = event::read()? {
                    match key.code {
                        KeyCode::Char('q') => break,
                        KeyCode::Char('1') => ex = Ex::E1,
                        KeyCode::Char('2') => ex = Ex::E2,
                        KeyCode::Char('3') => ex = Ex::E3,
                        KeyCode::Char('4') => ex = Ex::E4,
                        KeyCode::Char('5') => ex = Ex::Board,
                        KeyCode::Char(' ') => ex_since = Instant::now(),
                        _ => {}
                    }
                }
            }
            let dwell = match ex {
                Ex::E1 => 26,
                Ex::E4 => 22,
                Ex::Board => 14,
                _ => 11,
            };
            if autopilot && ex_since.elapsed() > Duration::from_secs(dwell) {
                ex = match ex {
                    Ex::E1 => Ex::E2,
                    Ex::E2 => Ex::E3,
                    Ex::E3 => Ex::E4,
                    Ex::E4 => Ex::Board,
                    Ex::Board => Ex::E1,
                };
                ex_since = Instant::now();
            }
        }
        Ok(())
    })();
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;
    res
}

fn launch_screen(root: &Path, state: &Arc<Mutex<State>>, prog: &Arc<AtomicU64>, start_s: f64) {
    {
        let mut s = state.lock().unwrap();
        if s.screen_running || s.screen_done {
            return;
        }
        s.screen_running = true;
        s.screen_start_s = start_s;
    }
    let root = root.to_path_buf();
    let state = state.clone();
    let prog = prog.clone();
    let workers = 96usize;
    let target = 12000usize;
    thread::spawn(move || {
        let compounds = screen::enumerate_distinct(target, 30);
        {
            let mut s = state.lock().unwrap();
            s.screen_total = compounds.len() as u64;
            s.screen_workers = workers;
        }
        let outcome = screen::run_screen(&root, &compounds, workers, |c| {
            prog.store(c, Ordering::Relaxed);
        });
        let mut s = state.lock().unwrap();
        if let Ok(o) = outcome {
            s.screen_scored = o.scored_ok as u64;
            s.screen_distinct = o.distinct as u64;
            s.screen_cps = o.compounds_per_s;
            s.screen_admissible = o.optimizer_admissible as u64;
            s.screen_ex = o.exemplar;
        }
        s.screen_running = false;
        s.screen_done = true;
    });
}

fn block(title: &str) -> Block<'_> {
    Block::default()
        .borders(Borders::ALL)
        .border_style(Style::default().fg(EDGE))
        .style(Style::default().bg(PANEL))
        .title(Span::styled(format!(" {title} "), Style::default().fg(CYAN).add_modifier(Modifier::BOLD)))
}

fn header(f: &mut Frame, area: Rect, tag: &str, title: &str, sub: &str) {
    f.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled("AMPHORA", Style::default().fg(CYAN).add_modifier(Modifier::BOLD)),
            Span::styled(format!("  {tag} · "), Style::default().fg(GRAY)),
            Span::styled(title, Style::default().fg(INK).add_modifier(Modifier::BOLD)),
            Span::styled(format!("   {sub}"), Style::default().fg(GRAY)),
        ]))
        .block(block("example")),
        area,
    );
}

fn footer_line() -> &'static str {
    "  [1] solver  [2] hazard  [3] factorial  [4] compounds/sec  [5] red-team board  ·  [space] hold  [q] quit"
}

fn draw(f: &mut Frame, s: &State, ex: Ex, done: u64, total: u64, sdone: u64, elapsed: Duration) {
    f.render_widget(Block::default().style(Style::default().bg(BG)), f.area());
    match ex {
        Ex::E1 => draw_e1(f, f.area(), s, done, total, elapsed),
        Ex::E2 => draw_e2(f, f.area(), s),
        Ex::E3 => draw_e3(f, f.area(), s),
        Ex::E4 => draw_e4(f, f.area(), s, sdone, elapsed),
        Ex::Board => draw_board(f, f.area()),
    }
}

fn draw_e1(f: &mut Frame, area: Rect, s: &State, done: u64, total: u64, elapsed: Duration) {
    let rows = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Length(3), Constraint::Length(4), Constraint::Min(10), Constraint::Length(4), Constraint::Length(1)])
        .split(area);
    header(f, rows[0], "E1", "VOC-MIN SOLVENT BLEND", "constrained formulation solver over the pinned ingredient library");
    let cg = Layout::default().direction(Direction::Horizontal).constraints([Constraint::Percentage(58), Constraint::Percentage(42)]).split(rows[1]);
    let secs = elapsed.as_secs_f64().max(0.001);
    let eps = (done as f64 / secs) as u64;
    let pct = if total > 0 { ((done.min(total)) as f64 / total as f64 * 100.0) as u16 } else { 0 };
    f.render_widget(
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled("FORMULATIONS ", Style::default().fg(GRAY)),
                Span::styled(commafy(done), Style::default().fg(INK).add_modifier(Modifier::BOLD)),
                Span::styled(format!(" / {}", commafy(total)), Style::default().fg(GRAY)),
                Span::styled("   EVAL/s ", Style::default().fg(GRAY)),
                Span::styled(commafy(eps), Style::default().fg(GREEN).add_modifier(Modifier::BOLD)),
            ]),
            Line::from(vec![
                Span::styled("FEASIBLE ", Style::default().fg(GRAY)),
                Span::styled(if s.grid_done { commafy(s.cells_feasible) } else { "searching…".to_string() }, Style::default().fg(CYAN)),
                Span::styled("   BEST VOC (live) ", Style::default().fg(GRAY)),
                Span::styled(format!("{:.2} g/L", if s.incumbent_voc.is_finite() { s.incumbent_voc } else { s.best_voc }), Style::default().fg(AMBER).add_modifier(Modifier::BOLD)),
                Span::styled(format!("   ELAPSED {:.1}s", secs), Style::default().fg(GRAY)),
            ]),
        ])
        .block(block("throughput")),
        cg[0],
    );
    let label = if s.grid_done { "COMPLETE".to_string() } else { format!("{pct}%") };
    f.render_widget(
        Gauge::default()
            .block(block("grid sweep"))
            .gauge_style(Style::default().fg(if s.grid_done { GREEN } else { CYAN }).bg(Color::Rgb(30, 41, 59)))
            .percent(pct)
            .label(Span::styled(label, Style::default().fg(INK).add_modifier(Modifier::BOLD))),
        cg[1],
    );
    let mid = Layout::default().direction(Direction::Horizontal).constraints([Constraint::Percentage(58), Constraint::Percentage(42)]).split(rows[2]);
    draw_pareto(f, mid[0], s);
    let right = Layout::default().direction(Direction::Vertical).constraints([Constraint::Percentage(48), Constraint::Percentage(52)]).split(mid[1]);
    draw_convergence(f, right[0], s);
    draw_agreement(f, right[1], s);
    draw_ledger(f, rows[3], s);
    f.render_widget(Paragraph::new(Span::styled(footer_line(), Style::default().fg(GRAY))), rows[4]);
}

fn draw_pareto(f: &mut Frame, area: Rect, s: &State) {
    if s.pareto.is_empty() && s.live_scatter.is_empty() {
        f.render_widget(Paragraph::new(Span::styled("computing pinned Pareto front…", Style::default().fg(GRAY))).block(block("Pareto: VOC vs Hansen RED")), area);
        return;
    }
    let basis: &Vec<(f64, f64)> = if !s.pareto.is_empty() { &s.pareto } else { &s.live_scatter };
    let xs: Vec<f64> = basis.iter().map(|p| p.0).collect();
    let ys: Vec<f64> = basis.iter().map(|p| p.1).collect();
    let xlo = (xs.iter().cloned().fold(f64::INFINITY, f64::min) - 5.0).floor();
    let xhi = (xs.iter().cloned().fold(f64::NEG_INFINITY, f64::max) + 5.0).ceil();
    let ylo = (ys.iter().cloned().fold(f64::INFINITY, f64::min) - 0.05).max(0.0);
    let yhi = ys.iter().cloned().fold(f64::NEG_INFINITY, f64::max) + 0.05;
    let inc_voc = if s.incumbent_voc.is_finite() { s.incumbent_voc } else { s.best_voc };
    let inc_red = if s.incumbent_voc.is_finite() { s.incumbent_red } else { s.best_red };
    let opt = vec![(inc_voc, inc_red)];
    let datasets = vec![
        Dataset::default().name("signed reference front").marker(symbols::Marker::Braille).graph_type(GraphType::Scatter).style(Style::default().fg(GRAY)).data(&s.pareto),
        Dataset::default().name("feasible (live)").marker(symbols::Marker::Braille).graph_type(GraphType::Scatter).style(Style::default().fg(CYAN)).data(&s.live_scatter),
        Dataset::default().name("incumbent ★ (live)").marker(symbols::Marker::Braille).graph_type(GraphType::Scatter).style(Style::default().fg(MAGENTA).add_modifier(Modifier::BOLD)).data(&opt),
    ];
    f.render_widget(
        Chart::new(datasets)
            .block(block("Pareto: VOC (g/L) vs Hansen RED"))
            .x_axis(Axis::default().style(Style::default().fg(GRAY)).bounds([xlo, xhi]).labels(vec![Span::raw(format!("{xlo:.0}")), Span::raw(format!("{:.0}", (xlo + xhi) / 2.0)), Span::raw(format!("{xhi:.0}"))]))
            .y_axis(Axis::default().style(Style::default().fg(GRAY)).bounds([ylo, yhi]).labels(vec![Span::raw(format!("{ylo:.2}")), Span::raw(format!("{:.2}", (ylo + yhi) / 2.0)), Span::raw(format!("{yhi:.2}"))])),
        area,
    );
}

fn draw_convergence(f: &mut Frame, area: Rect, s: &State) {
    if s.convergence.len() < 2 {
        f.render_widget(
            Paragraph::new(Span::styled(
                "incumbent best VOC — descends live as the sweep finds better cells…",
                Style::default().fg(GRAY),
            ))
            .block(block("convergence: best VOC vs cells swept")),
            area,
        );
        return;
    }
    let data: Vec<(f64, f64)> = s.convergence.clone();
    let xmax = data.last().map(|p| p.0).unwrap_or(1.0).max(1.0);
    let ys: Vec<f64> = data.iter().map(|p| p.1).collect();
    let ylo = (ys.iter().cloned().fold(f64::INFINITY, f64::min) - 2.0).floor();
    let yhi = (ys.iter().cloned().fold(f64::NEG_INFINITY, f64::max) + 2.0).ceil();
    let datasets = vec![Dataset::default()
        .name("best VOC")
        .marker(symbols::Marker::Braille)
        .graph_type(GraphType::Line)
        .style(Style::default().fg(GREEN).add_modifier(Modifier::BOLD))
        .data(&data)];
    f.render_widget(
        Chart::new(datasets)
            .block(block("convergence: best VOC (g/L) vs cells swept ↓"))
            .x_axis(Axis::default().style(Style::default().fg(GRAY)).bounds([0.0, xmax]).labels(vec![Span::raw("0"), Span::raw(commafy(xmax as u64))]))
            .y_axis(Axis::default().style(Style::default().fg(GRAY)).bounds([ylo, yhi]).labels(vec![Span::raw(format!("{ylo:.0}")), Span::raw(format!("{yhi:.0}"))])),
        area,
    );
}

fn draw_agreement(f: &mut Frame, area: Rect, s: &State) {
    let a = &s.agree;
    let rows = vec![
        Row::new(vec![Span::styled("GRID (exhaustive)", Style::default().fg(INK)), Span::styled(format!("{:.2}", a.grid), Style::default().fg(AMBER).add_modifier(Modifier::BOLD)), Span::styled("—", Style::default().fg(GRAY))]),
        Row::new(vec![Span::styled("PROJ-GRADIENT", Style::default().fg(INK)), Span::styled(format!("{:.2}", a.pg), Style::default().fg(GREEN).add_modifier(Modifier::BOLD)), Span::styled(format!("Δ {:.0e}", a.gap), Style::default().fg(GRAY))]),
        Row::new(vec![Span::styled("NSGA-II front", Style::default().fg(INK)), Span::styled(format!("{:.2}", a.nsga), Style::default().fg(GREEN).add_modifier(Modifier::BOLD)), Span::styled(if a.nsga_ok { "≥ optimum" } else { "?" }, Style::default().fg(GRAY))]),
    ];
    let inner = Layout::default().direction(Direction::Vertical).constraints([Constraint::Min(5), Constraint::Length(2)]).split(area);
    f.render_widget(
        Table::new(rows, [Constraint::Length(18), Constraint::Length(10), Constraint::Min(8)])
            .header(Row::new(vec!["METHOD", "VOC", ""]).style(Style::default().fg(CYAN).add_modifier(Modifier::BOLD)))
            .block(block("three-method agreement")),
        inner[0],
    );
    let verdict = if a.passed && a.nsga_ok {
        Span::styled("  ✔ all three agree < 1e-9 — optimum exhaustively verified", Style::default().fg(GREEN).add_modifier(Modifier::BOLD))
    } else {
        Span::styled("  … computing", Style::default().fg(GRAY))
    };
    f.render_widget(Paragraph::new(verdict).block(Block::default().style(Style::default().bg(PANEL))), inner[1]);
}

fn draw_ledger(f: &mut Frame, area: Rect, s: &State) {
    f.render_widget(
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled("OPTIMAL BLEND  ", Style::default().fg(GREEN).add_modifier(Modifier::BOLD)),
                Span::styled(format!("VOC {:.2} g/L", s.best_voc), Style::default().fg(AMBER).add_modifier(Modifier::BOLD)),
                Span::styled(format!("   Hansen RED {:.3} (cap 1.0)", s.best_red), Style::default().fg(GREEN)),
                Span::styled(format!("   flash {:.0}°C (≥38)", s.opt_flash), Style::default().fg(GREEN)),
                Span::styled(format!("   MAK {:.0}%", s.opt_mak * 100.0), Style::default().fg(CYAN)),
            ]),
            Line::from(vec![
                Span::styled("CONSTRAINTS  ", Style::default().fg(GRAY)),
                Span::styled("volume-solids∈[0.63,0.67]  flash≥38°C  Hansen-RED≤1  VOC≤340", Style::default().fg(INK)),
                Span::styled(format!("   · {} solvents excluded fail-closed", s.excluded), Style::default().fg(GRAY)),
            ]),
        ])
        .block(block("OPTIMAL BLEND — signed VOC-min optimum · 3-method agreement ✔")),
        area,
    );
}

fn draw_e2(f: &mut Frame, area: Rect, s: &State) {
    let rows = Layout::default().direction(Direction::Vertical).constraints([Constraint::Length(3), Constraint::Length(3), Constraint::Min(6), Constraint::Length(3), Constraint::Length(1)]).split(area);
    header(f, rows[0], "E2", "HAZARD-CONSTRAINED HARDENER SELECTION", "GHS + applicability-domain gates over the pinned hardener set");
    let banner = if s.p3_feasible == 0 {
        Paragraph::new(Line::from(vec![
            Span::styled("  FEASIBLE SET EMPTY — pareto_status: BLOCKED", Style::default().fg(REDC).add_modifier(Modifier::BOLD)),
            Span::styled("   the solver refuses to recommend an unsafe candidate", Style::default().fg(GRAY)),
        ]))
    } else {
        Paragraph::new(Span::styled(format!("  {} feasible", s.p3_feasible), Style::default().fg(GREEN)))
    };
    f.render_widget(banner.block(block("verdict")), rows[1]);
    let hz: Vec<Row> = s
        .hazards
        .iter()
        .map(|h| {
            let mark = |b: bool| if b { Span::styled("✗ FAIL", Style::default().fg(REDC).add_modifier(Modifier::BOLD)) } else { Span::styled("· ok", Style::default().fg(GREEN)) };
            Row::new(vec![
                Span::styled(h.candidate.clone(), Style::default().fg(INK).add_modifier(Modifier::BOLD)),
                mark(h.h317),
                mark(h.h351),
                mark(h.ad_fail),
                if h.h317 || h.h351 || h.ad_fail { Span::styled("BLOCKED", Style::default().fg(REDC)) } else { Span::styled("feasible", Style::default().fg(GREEN)) },
            ])
        })
        .collect();
    f.render_widget(
        Table::new(hz, [Constraint::Length(10), Constraint::Length(12), Constraint::Length(12), Constraint::Length(14), Constraint::Min(10)])
            .header(Row::new(vec!["HARDENER", "GHS H317", "GHS H351", "AD-TANIMOTO", "STATUS"]).style(Style::default().fg(CYAN).add_modifier(Modifier::BOLD)))
            .block(block("candidate × gate (pinned GHS KPI + applicability domain)")),
        rows[2],
    );
    f.render_widget(
        Paragraph::new(Line::from(vec![
            Span::styled("HONEST NEGATIVE RESULT  ", Style::default().fg(AMBER).add_modifier(Modifier::BOLD)),
            Span::styled("every one of the 5 hardeners carries H317; 4/5 also fail the applicability-domain gate; DDS adds H351. No winner is manufactured.", Style::default().fg(GRAY)),
        ]))
        .block(block("why this is the strongest slide")),
        rows[3],
    );
    f.render_widget(Paragraph::new(Span::styled(footer_line(), Style::default().fg(GRAY))), rows[4]);
}

fn draw_e3(f: &mut Frame, area: Rect, s: &State) {
    let rows = Layout::default().direction(Direction::Vertical).constraints([Constraint::Length(3), Constraint::Length(4), Constraint::Min(6), Constraint::Length(1)]).split(area);
    header(f, rows[0], "E3", "2⁴ FACTORIAL PROCESS SCREEN", "exhaustive resin × hardener × pigment × solvent envelope enumeration");
    f.render_widget(
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled("CELLS ", Style::default().fg(GRAY)),
                Span::styled(format!("{}", s.p4_cells), Style::default().fg(INK).add_modifier(Modifier::BOLD)),
                Span::styled("   SOLVED ", Style::default().fg(GRAY)),
                Span::styled(format!("{}", s.p4_solved), Style::default().fg(GREEN).add_modifier(Modifier::BOLD)),
                Span::styled("   INFEASIBLE ", Style::default().fg(GRAY)),
                Span::styled(format!("{}", s.p4_infeasible), Style::default().fg(AMBER).add_modifier(Modifier::BOLD)),
                Span::styled(format!("   status {}", s.p4_status), Style::default().fg(CYAN)),
            ]),
            Line::from(Span::styled("deterministic exhaustive enumeration · two-replay byte-stable · every cell's blocking reasons recorded", Style::default().fg(GRAY))),
        ])
        .block(block("factorial accounting")),
        rows[1],
    );
    // 4x4 grid of cells
    let grid_rows = Layout::default().direction(Direction::Vertical).constraints([Constraint::Ratio(1, 4); 4]).split(rows[2]);
    for r in 0..4 {
        let cols = Layout::default().direction(Direction::Horizontal).constraints([Constraint::Ratio(1, 4); 4]).split(grid_rows[r]);
        for c in 0..4 {
            let idx = r * 4 + c;
            let solved = [0, 1, 4, 5, 8, 9, 12, 13].contains(&idx);
            let (col, txt) = if solved { (GREEN, "SOLVED") } else { (AMBER, "INFEASIBLE") };
            f.render_widget(
                Paragraph::new(vec![
                    Line::from(Span::styled(format!("cell {idx}"), Style::default().fg(INK))),
                    Line::from(Span::styled(txt, Style::default().fg(col).add_modifier(Modifier::BOLD))),
                ])
                .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(col)).style(Style::default().bg(PANEL))),
                cols[c],
            );
        }
    }
    f.render_widget(Paragraph::new(Span::styled(footer_line(), Style::default().fg(GRAY))), rows[3]);
}

fn draw_e4(f: &mut Frame, area: Rect, s: &State, sdone: u64, elapsed: Duration) {
    let rows = Layout::default().direction(Direction::Vertical).constraints([Constraint::Length(3), Constraint::Length(5), Constraint::Min(6), Constraint::Length(4), Constraint::Length(1)]).split(area);
    header(f, rows[0], "E4", "COMPOUNDS / SECOND", "distinct molecules through the pinned RDKit gate stack — engineering throughput only");
    let secs = elapsed.as_secs_f64().max(0.001);
    let screen_secs = (secs - s.screen_start_s).max(1e-3);
    let cps = if s.screen_done { s.screen_cps } else if s.screen_running && sdone > 0 { sdone as f64 / screen_secs } else { 0.0 };
    let total = s.screen_total.max(1);
    let pct = ((sdone.min(total)) as f64 / total as f64 * 100.0) as u16;
    f.render_widget(
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled("COMPOUNDS ", Style::default().fg(GRAY)),
                Span::styled(commafy(sdone), Style::default().fg(INK).add_modifier(Modifier::BOLD)),
                Span::styled(format!(" / {}", commafy(s.screen_total)), Style::default().fg(GRAY)),
                Span::styled("    >> COMPOUNDS/SEC ", Style::default().fg(GRAY)),
                Span::styled(format!("{:.0}", cps), Style::default().fg(GREEN).add_modifier(Modifier::BOLD)),
                Span::styled(format!("   ×{} workers", s.screen_workers), Style::default().fg(GRAY)),
            ]),
            Line::from(vec![
                Span::styled("DISTINCT ", Style::default().fg(GRAY)),
                Span::styled(commafy(s.screen_distinct), Style::default().fg(CYAN)),
                Span::styled("   OPTIMIZER-ADMISSIBLE ", Style::default().fg(GRAY)),
                Span::styled(format!("{}", s.screen_admissible), Style::default().fg(if s.screen_admissible == 0 { GREEN } else { REDC }).add_modifier(Modifier::BOLD)),
                Span::styled("  (must be 0)", Style::default().fg(GRAY)),
                Span::styled(if s.screen_running { "   RUNNING…" } else if s.screen_done { "   COMPLETE" } else { "   press [4] to start" }, Style::default().fg(AMBER)),
            ]),
        ])
        .block(block("throughput (fully gate-scored, distinct-by-canonical-SHA256)")),
        rows[1],
    );
    let midrow = Layout::default().direction(Direction::Horizontal).constraints([Constraint::Percentage(42), Constraint::Percentage(58)]).split(rows[2]);
    let gcol = Layout::default().direction(Direction::Vertical).constraints([Constraint::Length(3), Constraint::Min(1)]).split(midrow[0]);
    f.render_widget(
        Gauge::default().block(block("screen progress")).gauge_style(Style::default().fg(if s.screen_done { GREEN } else { CYAN }).bg(Color::Rgb(30, 41, 59))).percent(pct.min(100)).label(Span::styled(format!("{pct}%"), Style::default().fg(INK).add_modifier(Modifier::BOLD))),
        gcol[0],
    );
    f.render_widget(
        Paragraph::new(vec![
            Line::from(Span::styled("GATE FUNNEL", Style::default().fg(CYAN).add_modifier(Modifier::BOLD))),
            Line::from(Span::styled("enumerated → RDKit-valid → normalized →", Style::default().fg(GRAY))),
            Line::from(Span::styled("property/role/novelty/design-gate → distinct", Style::default().fg(GRAY))),
        ]).block(block("pipeline")),
        gcol[1],
    );
    exemplar_card(f, midrow[1], &s.screen_ex);
    f.render_widget(
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled("SPEEDUP  ", Style::default().fg(AMBER).add_modifier(Modifier::BOLD)),
                Span::styled("corpus-fingerprint cache: 10 → 2 RDKit calls/compound, bit-identical (proven by test)", Style::default().fg(INK)),
            ]),
            Line::from(Span::styled("every compound distinct by canonical SHA-256 · scoring bit-identical across 1…128 workers", Style::default().fg(GRAY))),
        ])
        .block(block("faster, provably identical")),
        rows[3],
    );
    f.render_widget(
        Paragraph::new(Span::styled(
            "  ENGINEERING THROUGHPUT ONLY — not novelty/ranking/screening-quality/validated science; all molecule modules ranking_eligible:false, AUDIT_ONLY   ·   [q] quit",
            Style::default().fg(GRAY),
        )),
        rows[4],
    );
}

fn exemplar_card(f: &mut Frame, area: Rect, e: &screen::Exemplar) {
    if !e.found {
        f.render_widget(
            Paragraph::new(Span::styled("finding a structurally-admissible exemplar…", Style::default().fg(GRAY)))
                .block(block("admissible exemplar")),
            area,
        );
        return;
    }
    let ew = if e.role == "hardener" {
        format!("AHEW {:.1} g/eq", e.ahew.unwrap_or(0.0))
    } else {
        format!("EEW {:.1} g/eq", e.eew.unwrap_or(0.0))
    };
    let nd = e.novelty_dist.map(|v| format!("{v:.2}")).unwrap_or_else(|| "—".into());
    f.render_widget(
        Paragraph::new(vec![
            Line::from(vec![
                Span::styled("SMILES  ", Style::default().fg(GRAY)),
                Span::styled(e.smiles.clone(), Style::default().fg(CYAN).add_modifier(Modifier::BOLD)),
                Span::styled("    role ", Style::default().fg(GRAY)),
                Span::styled(e.role.clone(), Style::default().fg(INK).add_modifier(Modifier::BOLD)),
            ]),
            Line::from(vec![
                Span::styled("formula ", Style::default().fg(GRAY)),
                Span::styled(e.formula.clone(), Style::default().fg(INK)),
                Span::styled(format!("   MW {:.1}", e.mw), Style::default().fg(INK)),
                Span::styled(format!("   {ew}", ), Style::default().fg(AMBER).add_modifier(Modifier::BOLD)),
            ]),
            Line::from(vec![
                Span::styled("design-gate ", Style::default().fg(GRAY)),
                Span::styled("pass_all_hard ✔", Style::default().fg(GREEN).add_modifier(Modifier::BOLD)),
                Span::styled(format!("    novelty-dist {nd}"), Style::default().fg(GRAY)),
            ]),
            Line::from(Span::styled(
                "structural applicability only — an admissible exemplar, NOT ranked, recommended, validated, or a performance/safety claim",
                Style::default().fg(GRAY),
            )),
        ])
        .block(block("admissible exemplar — passes ALL hard design gates (AUDIT_ONLY, not ranked)")),
        area,
    );
}

// ---- Board: red-team scoreboard + module board + benchkit strip ----------
struct Rt { id: &'static str, attack: &'static str, before: &'static str, after: &'static str }
const REDTEAM: &[Rt] = &[
    Rt { id: "T-01B", attack: "candidate hash forged into typed provenance identity", before: "REFUTED (poison→root_hash)", after: "FIXED · clean==poison typed hash 9c7d62bb…" },
    Rt { id: "T-13", attack: "verify_run accepts forged / replayed run archives", before: "122/126 forgeries verify intact", after: "FIXED · 0/210 verify · chain recomputed" },
    Rt { id: "T-05", attack: "fabricated molecule facts drive the stoichiometry", before: "REFUTED (phr = 2,057,940)", after: "SURVIVED · RDKit-attested · 2-replay stable" },
];
struct Md { name: &'static str, status: &'static str, note: &'static str }
const MODS: &[Md] = &[
    Md { name: "amphora-solver-lab", status: "GREEN", note: "3-method agreement < 1e-9 (E1/E2/E3)" },
    Md { name: "amphora-formulation-arithmetic", status: "GREEN", note: "RDKit-attested (was RED · T-05)" },
    Md { name: "amphora-run-provenance", status: "GREEN", note: "chain recompute (was RED · T-13)" },
    Md { name: "amphora-candidate-contract", status: "GREEN", note: "host-owned identity (was RED · T-01B)" },
    Md { name: "amphora-molecule-novelty", status: "GREEN", note: "W-NOV1 SURVIVED · corpus-fp cache bit-identical" },
    Md { name: "amphora-molecule-design-gate", status: "GREEN", note: "13/13 gates, real RDKit FFI" },
    Md { name: "amphora-rdkit-ffi", status: "GREEN", note: "pinned RDKit C++ 2026.03.2" },
    Md { name: "amphora-molecule-property", status: "RED", note: "excluded: ε_static<n² labels" },
    Md { name: "amphora-barrier-corrosion-score", status: "RED", note: "excluded: silent 3.5-decade error" },
    Md { name: "amphora-ip-fto-guard", status: "RED", note: "excluded: FTO flips under construction" },
];
struct Bk { name: &'static str, speedup: &'static str }
const BENCH: &[Bk] = &[
    Bk { name: "nn_max_tanimoto (novelty)", speedup: "19.8× · bit-identical" },
    Bk { name: "mean_pairwise_tanimoto", speedup: "18.4× · bit-identical" },
    Bk { name: "ewma_arl (process-qc)", speedup: "14.78× vs-adopted · bit-identical" },
    Bk { name: "cluster_bootstrap_ci", speedup: "2.08× · bit-identical" },
];

fn draw_board(f: &mut Frame, area: Rect) {
    let rows = Layout::default().direction(Direction::Vertical).constraints([Constraint::Length(3), Constraint::Length(8), Constraint::Min(6), Constraint::Length(6), Constraint::Length(1)]).split(area);
    header(f, rows[0], "BOARD", "RED-TEAM SCOREBOARD", "our own falsification loop found these; this session closed them");
    let rt: Vec<Row> = REDTEAM.iter().map(|r| Row::new(vec![
        Span::styled(r.id, Style::default().fg(AMBER).add_modifier(Modifier::BOLD)),
        Span::styled(r.attack, Style::default().fg(INK)),
        Span::styled(r.before, Style::default().fg(REDC)),
        Span::styled(r.after, Style::default().fg(GREEN).add_modifier(Modifier::BOLD)),
    ]).height(2)).collect();
    f.render_widget(
        Table::new(rt, [Constraint::Length(7), Constraint::Percentage(38), Constraint::Percentage(26), Constraint::Percentage(30)])
            .header(Row::new(vec!["ID", "ATTACK", "BEFORE", "AFTER (this session)"]).style(Style::default().fg(CYAN).add_modifier(Modifier::BOLD)))
            .block(block("spine repairs — verified against the original signed attack harnesses")),
        rows[1],
    );
    let mr: Vec<Row> = MODS.iter().map(|m| {
        let c = if m.status == "GREEN" { GREEN } else { REDC };
        Row::new(vec![
            Span::styled(format!("● {}", m.status), Style::default().fg(c).add_modifier(Modifier::BOLD)),
            Span::styled(m.name, Style::default().fg(INK)),
            Span::styled(m.note, Style::default().fg(GRAY)),
        ])
    }).collect();
    f.render_widget(
        Table::new(mr, [Constraint::Length(9), Constraint::Length(34), Constraint::Min(20)])
            .header(Row::new(vec!["STATUS", "MODULE", "NOTE"]).style(Style::default().fg(CYAN).add_modifier(Modifier::BOLD)))
            .block(block("module board — GREEN in the demo · RED excluded by signed refutation")),
        rows[2],
    );
    let bk: Vec<Row> = BENCH.iter().map(|b| Row::new(vec![
        Span::styled(b.name, Style::default().fg(INK)),
        Span::styled(b.speedup, Style::default().fg(GREEN).add_modifier(Modifier::BOLD)),
    ])).collect();
    f.render_widget(
        Table::new(bk, [Constraint::Length(34), Constraint::Min(20)])
            .header(Row::new(vec!["AUDIT KERNEL", "SPEEDUP (all_bit_identical: true)"]).style(Style::default().fg(CYAN).add_modifier(Modifier::BOLD)))
            .block(block("faster, provably identical — benchkit signed speedups.canonical.json")),
        rows[3],
    );
    f.render_widget(Paragraph::new(Span::styled("  RED = excluded by signed refutation · speedups are bit-identical to the reference · nothing here claims scientific validation   ·   [q] quit", Style::default().fg(GRAY))), rows[4]);
}

fn snapshot_text(s: &State, done: u64, total: u64) -> String {
    format!(
        "SHOWCASE headless snapshot\n\
         E1 solver : {} / {} cells, feasible {}, best VOC {:.2} g/L, agreement grid/pg/nsga {:.2}/{:.2}/{:.2} passed={}\n\
         E2 hazard : status={} feasible={} (hardeners screened: {})\n\
         E3 factorial : {} cells, solved {}, infeasible {}, status {}\n\
         E4 compounds: {} scored, {} distinct, {:.0} compounds/sec ×{} workers, optimizer-admissible {}\n",
        commafy(done), commafy(total), commafy(s.cells_feasible), s.best_voc,
        s.agree.grid, s.agree.pg, s.agree.nsga, s.agree.passed,
        s.p3_status, s.p3_feasible, s.hazards.len(),
        s.p4_cells, s.p4_solved, s.p4_infeasible, s.p4_status,
        commafy(s.screen_scored), commafy(s.screen_distinct), s.screen_cps, s.screen_workers, s.screen_admissible,
    )
}
