use amphora_core::{ModuleTelemetry, RankedCandidate, ScoreHistory, Throughput};
use anyhow::Result;
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
    widgets::{
        Axis, Block, Borders, Cell, Chart, Clear, Dataset, GraphType, Paragraph, Row, Table,
        TableState, Wrap,
    },
    Terminal,
};
use std::collections::BTreeSet;
use std::io::{self, IsTerminal};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::Receiver;
use std::sync::Arc;

const TOP_CANDIDATES: usize = 10;
const MAX_CHART_CANDIDATES: usize = 5;

#[derive(Debug, Clone)]
pub struct DashboardState {
    pub run_id: String,
    pub generation: u32,
    pub generations: u32,
    pub phase: String,
    pub scoring_completed: usize,
    pub scoring_total: usize,
    pub rejected_candidates: u64,
    pub worker_failures: u64,
    pub elapsed_ms: u128,
    pub throughput: Throughput,
    pub active_workers: usize,
    pub registered_modules: usize,
    pub active_modules: usize,
    pub modules: Vec<ModuleTelemetry>,
    pub candidates: Vec<RankedCandidate>,
    pub history: Vec<ScoreHistory>,
    pub selected_candidate: Option<String>,
    pub paused: bool,
    pub objective_ready: bool,
    pub finished: bool,
    pub logs: Vec<String>,
}

pub fn state_text(state: &DashboardState) -> String {
    let rates = state.throughput.run_rates(amphora_core::now_ms());
    let mut out = String::new();
    out.push_str(&format!(
        "AMPHORA MVP20 — RUN {} — GEN {}/{} — {} ms\n",
        state.run_id, state.generation, state.generations, state.elapsed_ms
    ));
    out.push_str(&format!(
        "PHASE {} · {}/{} | rejected {} | worker failures {}\n",
        phase_label(&state.phase),
        state.scoring_completed,
        state.scoring_total,
        state.rejected_candidates,
        state.worker_failures
    ));
    out.push_str(&format!(
        "Throughput / Population | attempts/s {:.2} | valid/s {:.2} | scored/s {:.2} | survivors/s {:.2} | solutions/s {:.2}\n",
        rates[0], rates[1], rates[2], rates[3], rates[4]
    ));
    out.push_str(&format!(
        "Attempted {}  Valid {}  Scored {}  Survivors {}  Solutions {}  Active workers {}\n",
        state.throughput.attempted,
        state.throughput.valid,
        state.throughput.scored,
        state.throughput.survivors,
        state.throughput.solutions,
        state.active_workers
    ));
    out.push_str(&format!(
        "Registered modules: {} | Active molecule submodels: {} | Scored on latest candidate: {}/{}\n",
        state.registered_modules,
        state.active_modules,
        state.modules.iter().filter(|m| m.last_status == "SCORED").count(),
        state.active_modules
    ));
    out.push_str("LIVE SCORE HISTORY\n");
    if let Some(point) = state.history.last() {
        out.push_str(&format!(
            "generation={} best={} mean={} feasible={} ranked={} snapshots={}\n",
            point.generation,
            format_score(point.best_feasible_score),
            format_score(point.mean_feasible_score),
            point.feasible_count,
            point.ranked_count,
            state.history.len()
        ));
    } else {
        out.push_str("No ranked snapshots yet.\n");
    }
    if state.candidates.is_empty() && state.phase == "SCORING_INITIAL_POPULATION" {
        out.push_str(&format!(
            "SCORING INITIAL POPULATION — {}/{}\n",
            state.scoring_completed, state.scoring_total
        ));
    } else if state.candidates.is_empty() {
        out.push_str("TOP 10 CANDIDATES — NO RANKED RESULTS\n");
    } else if state.objective_ready {
        out.push_str("TOP 10 CANDIDATES — PARETO RANKED\n");
    } else {
        out.push_str("TOP 10 CANDIDATES — OBJECTIVES PENDING\n");
    }
    let visible_candidates = state
        .candidates
        .iter()
        .take(TOP_CANDIDATES)
        .collect::<Vec<_>>();
    let visible_ids = short_ids(
        visible_candidates
            .iter()
            .map(|candidate| candidate.candidate_id.as_str()),
    );
    for (index, candidate) in visible_candidates.iter().enumerate() {
        out.push_str(&format_candidate_text(
            index,
            candidate,
            &visible_ids[index],
        ));
    }
    if let Some(candidate) = selected_candidate(state) {
        out.push_str("\nSELECTED CANDIDATE PREVIEW\n");
        append_preview_text(&mut out, candidate);
    }
    out.push_str("\nSubmodel Fleet\nMODULE                                  STATUS              SCORED  LAST       LATENCY\n");
    for module in &state.modules {
        out.push_str(&format!(
            "{:<40} {:<19} {:>4}     {:<9} {:>4} ms\n",
            module.module_id,
            module.last_status,
            module.scored_count,
            module
                .last_score
                .map(|s| format!("{s:.3}"))
                .unwrap_or_else(|| "—".into()),
            module.last_latency_ms
        ));
    }
    out.push_str("\nSelected Candidate / Lineage / KPI Details\n");
    out.push_str(&format!(
        "selected={} | q quit  p pause  r restart  m modules  s sort  Enter inspect  Esc close\n",
        state
            .selected_candidate
            .as_deref()
            .map(short_id)
            .unwrap_or_else(|| "none".into())
    ));
    out.push_str("\nSOLVER LOG\n");
    for log in state.logs.iter().rev().take(8).rev() {
        out.push_str(&format!("[INFO] {log}\n"));
    }
    out
}

fn format_candidate_text(index: usize, candidate: &RankedCandidate, display_id: &str) -> String {
    let rank = candidate
        .current_rank
        .map(|value| value.to_string())
        .unwrap_or_else(|| "—".into());
    let delta = candidate
        .rank_delta
        .map(|value| format!("{value:+}"))
        .unwrap_or_else(|| "—".into());
    let score = format_score(candidate.moo_display_score);
    let role_fit = objective_value(candidate, "role_fit");
    let novelty = objective_value(candidate, "novelty_score");
    format!(
        "{:>2}. rank={:<3} prev={:<3} {} {:<3} {:<18} score={} role-fit={} novelty={} gate={} marker={}\n",
        index + 1,
        rank,
        candidate
            .previous_rank
            .map(|value| value.to_string())
            .unwrap_or_else(|| "—".into()),
        candidate.movement,
        delta,
        display_id,
        score,
        role_fit,
        novelty,
        if candidate.feasible { "PASS" } else { "FAIL" },
        if candidate.mutation_id.is_some() { "MUTATION" } else { "SURVIVOR" },
    )
}

fn phase_label(phase: &str) -> String {
    phase.replace('_', " ")
}

fn format_score(value: Option<f64>) -> String {
    value
        .map(|value| format!("{value:.3}"))
        .unwrap_or_else(|| "—".into())
}

fn objective_value(candidate: &RankedCandidate, id: &str) -> String {
    candidate
        .objective_rows
        .iter()
        .find(|row| row.id == id)
        .map(|row| format!("{:.3}", row.value))
        .unwrap_or_else(|| "—".into())
}

fn kpi_value(candidate: &RankedCandidate, id: &str) -> Option<String> {
    candidate
        .display_kpis
        .iter()
        .find(|kpi| kpi.id == id)
        .map(|kpi| format!("{}={}", kpi.label, compact_json(&kpi.value)))
}

fn selected_candidate(state: &DashboardState) -> Option<&RankedCandidate> {
    state
        .selected_candidate
        .as_deref()
        .and_then(|id| {
            state
                .candidates
                .iter()
                .find(|candidate| candidate.candidate_id == id)
        })
        .or_else(|| state.candidates.first())
}

fn append_preview_text(out: &mut String, candidate: &RankedCandidate) {
    if let Some(preview) = &candidate.chemical_preview {
        out.push_str(&format!(
            "{} | role={} | {}\n",
            preview.name, preview.role, preview.render_status
        ));
        for line in &preview.ascii_lines {
            out.push_str(line);
            out.push('\n');
        }
        out.push_str(&format!("SMILES: {}\n", preview.canonical_smiles));
    } else {
        out.push_str("Chemical preview unavailable.\n");
    }
}

pub fn run_dashboard(state: &DashboardState) -> Result<()> {
    if !io::stdout().is_terminal() {
        print!("{}", state_text(state));
        return Ok(());
    }
    let cancel = Arc::new(AtomicBool::new(false));
    let (sender, receiver) = std::sync::mpsc::channel();
    sender.send(state.clone()).ok();
    drop(sender);
    run_live_dashboard(receiver, cancel, 100)
}

pub fn run_live_dashboard(
    receiver: Receiver<DashboardState>,
    cancel: Arc<AtomicBool>,
    refresh_ms: u64,
) -> Result<()> {
    if !io::stdout().is_terminal() {
        if let Ok(state) = receiver.recv() {
            print!("{}", state_text(&state));
        }
        return Ok(());
    }
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    let result = draw_live_until_quit(&mut terminal, receiver, cancel, refresh_ms);
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;
    result
}

struct DashboardApp {
    state: Option<DashboardState>,
    selected: Option<String>,
    modal_open: bool,
}

impl DashboardApp {
    fn new() -> Self {
        Self {
            state: None,
            selected: None,
            modal_open: false,
        }
    }

    fn update(&mut self, mut state: DashboardState) {
        let selected = self
            .selected
            .clone()
            .or_else(|| state.selected_candidate.clone());
        let selected = selected.filter(|id| {
            state
                .candidates
                .iter()
                .take(TOP_CANDIDATES)
                .any(|candidate| &candidate.candidate_id == id)
        });
        self.selected =
            selected.or_else(|| state.candidates.first().map(|c| c.candidate_id.clone()));
        state.selected_candidate = self.selected.clone();
        self.state = Some(state);
    }

    fn move_selection(&mut self, offset: isize) {
        let Some(state) = &self.state else { return };
        let count = state.candidates.len().min(TOP_CANDIDATES);
        if count == 0 {
            return;
        }
        let current = self
            .selected
            .as_ref()
            .and_then(|id| {
                state
                    .candidates
                    .iter()
                    .take(count)
                    .position(|c| &c.candidate_id == id)
            })
            .unwrap_or(0) as isize;
        let next = (current + offset).rem_euclid(count as isize) as usize;
        self.selected = Some(state.candidates[next].candidate_id.clone());
        if let Some(state) = &mut self.state {
            state.selected_candidate = self.selected.clone();
        }
    }

    fn selected(&self) -> Option<&RankedCandidate> {
        let state = self.state.as_ref()?;
        self.selected.as_deref().and_then(|id| {
            state
                .candidates
                .iter()
                .find(|candidate| candidate.candidate_id == id)
        })
    }
}

fn draw_live_until_quit(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    receiver: Receiver<DashboardState>,
    cancel: Arc<AtomicBool>,
    refresh_ms: u64,
) -> Result<()> {
    let mut app = DashboardApp::new();
    let mut disconnected = false;
    loop {
        match receiver.recv_timeout(std::time::Duration::from_millis(refresh_ms.clamp(10, 250))) {
            Ok(state) => {
                app.update(state);
                for state in receiver.try_iter() {
                    app.update(state);
                }
            }
            Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => disconnected = true,
            Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {}
        }
        terminal.draw(|frame| draw_frame(frame, &app))?;
        if event::poll(std::time::Duration::from_millis(20))? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') => {
                        cancel.store(true, Ordering::SeqCst);
                        break;
                    }
                    KeyCode::Up => app.move_selection(-1),
                    KeyCode::Down => app.move_selection(1),
                    KeyCode::Enter if app.selected().is_some() => app.modal_open = true,
                    KeyCode::Esc if app.modal_open => app.modal_open = false,
                    _ => {}
                }
            }
        }
        if disconnected && app.state.as_ref().is_none() {
            break;
        }
    }
    Ok(())
}

fn draw_frame(frame: &mut ratatui::Frame<'_>, app: &DashboardApp) {
    let area = frame.area();
    frame.render_widget(
        Block::default().style(Style::default().bg(Color::Rgb(8, 16, 29))),
        area,
    );
    let Some(state) = &app.state else {
        frame.render_widget(
            Paragraph::new("Waiting for registry and scoring snapshots…")
                .style(Style::default().fg(Color::Gray))
                .block(panel_block("AMPHORA MVP20")),
            area,
        );
        return;
    };
    let compact = area.height < 34;
    let vertical = Layout::default()
        .direction(Direction::Vertical)
        .constraints(if compact {
            [
                Constraint::Length(3),
                Constraint::Length(8),
                Constraint::Min(8),
                Constraint::Length(4),
            ]
        } else {
            [
                Constraint::Length(3),
                Constraint::Length(11),
                Constraint::Min(14),
                Constraint::Length(6),
            ]
        })
        .split(area);
    let header = Paragraph::new(Line::from(vec![
        Span::styled(
            " AMPHORA MVP20 ",
            Style::default()
                .fg(Color::Rgb(8, 16, 29))
                .bg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        ),
        Span::styled(
            format!(
                " RUN {}  GEN {}/{}  {} ms  {}",
                state.run_id,
                state.generation,
                state.generations,
                state.elapsed_ms,
                if state.finished { "COMPLETE" } else { "LIVE" }
            ),
            Style::default().fg(Color::Gray),
        ),
    ]))
    .block(panel_block("RUN STATUS"));
    frame.render_widget(header, vertical[0]);

    let upper = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(28), Constraint::Percentage(72)])
        .split(vertical[1]);
    let rates = state.throughput.run_rates(amphora_core::now_ms());
    let throughput = Paragraph::new(vec![
        Line::from(vec![
            Span::styled("PHASE ", Style::default().fg(Color::Gray)),
            Span::styled(
                format!(
                    "{} · {}/{}",
                    phase_label(&state.phase),
                    state.scoring_completed,
                    state.scoring_total
                ),
                Style::default().fg(if state.phase.starts_with("SCORING") {
                    Color::Yellow
                } else if state.finished {
                    Color::Green
                } else {
                    Color::Cyan
                }),
            ),
        ]),
        Line::from(Span::styled(
            format!(
                "{} {}/{}",
                progress_bar(state.scoring_completed, state.scoring_total, 12),
                state.scoring_completed,
                state.scoring_total
            ),
            Style::default().fg(Color::Yellow),
        )),
        Line::from(format!("attempts/s {:>8.2}", rates[0])),
        Line::from(format!("valid/s    {:>8.2}", rates[1])),
        Line::from(format!("scored/s   {:>8.2}", rates[2])),
        Line::from(format!("solutions/s {:>7.2}", rates[4])),
        Line::from(format!(
            "Attempted {} Valid {} Scored {}",
            state.throughput.attempted, state.throughput.valid, state.throughput.scored
        )),
        Line::from(format!(
            "Rejects {} Failures {}",
            state.rejected_candidates, state.worker_failures
        )),
        Line::from(format!(
            "Workers {} Submodels {}/{}",
            state.active_workers, state.active_modules, state.registered_modules
        )),
    ])
    .style(Style::default().fg(Color::Gray))
    .block(panel_block("THROUGHPUT / POPULATION"))
    .wrap(Wrap { trim: true });
    frame.render_widget(throughput, upper[0]);
    draw_history_chart(frame, upper[1], state, app.selected.as_deref());

    let middle = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(65), Constraint::Percentage(35)])
        .split(vertical[2]);
    draw_ranking_table(frame, middle[0], state, app.selected.as_deref());
    draw_candidate_context(frame, middle[1], state, app.selected.as_deref());

    let mut module_lines = state
        .modules
        .iter()
        .take(3)
        .map(|m| {
            Line::from(vec![
                Span::styled(
                    format!("{} ", short_id(&m.module_id)),
                    Style::default().fg(Color::Gray),
                ),
                Span::styled(
                    format!(
                        "{} {}/{} {} ms",
                        m.last_status, m.scored_count, m.attempted_count, m.last_latency_ms
                    ),
                    Style::default().fg(if m.last_status == "SCORED" {
                        Color::Green
                    } else if m.last_status == "ERROR" {
                        Color::Red
                    } else {
                        Color::Yellow
                    }),
                ),
            ])
        })
        .collect::<Vec<_>>();
    module_lines.push(Line::from(Span::styled(
        "STATUS: green=pass cyan=live amber=scoring magenta=mutation red=failure",
        Style::default()
            .fg(Color::Magenta)
            .add_modifier(Modifier::BOLD),
    )));
    module_lines.extend(
        state
            .logs
            .iter()
            .rev()
            .take(if compact { 0 } else { 2 })
            .rev()
            .map(|log| {
                let color = if log.contains("complete") {
                    Color::Green
                } else if log.contains("scoring") {
                    Color::Yellow
                } else if log.contains("proposing") {
                    Color::Magenta
                } else {
                    Color::Gray
                };
                Line::from(Span::styled(log.clone(), Style::default().fg(color)))
            }),
    );
    frame.render_widget(
        Paragraph::new(module_lines)
            .style(Style::default().fg(Color::Gray))
            .block(panel_block("SUBMODEL FLEET"))
            .wrap(Wrap { trim: true }),
        vertical[3],
    );
    if app.modal_open {
        if let Some(candidate) = app.selected() {
            draw_candidate_modal(frame, area, state, candidate);
        }
    }
}

fn panel_block(title: impl Into<Line<'static>>) -> Block<'static> {
    Block::default()
        .borders(Borders::ALL)
        .border_style(Style::default().fg(Color::Rgb(71, 91, 116)))
        .style(Style::default().bg(Color::Rgb(15, 29, 48)))
        .title(title)
}

fn progress_bar(completed: usize, total: usize, width: usize) -> String {
    let filled = completed
        .saturating_mul(width)
        .min(total.saturating_mul(width))
        .checked_div(total)
        .unwrap_or(0);
    format!(
        "[{}{}]",
        "━".repeat(filled),
        "·".repeat(width.saturating_sub(filled))
    )
}

fn draw_history_chart(
    frame: &mut ratatui::Frame<'_>,
    area: Rect,
    state: &DashboardState,
    selected: Option<&str>,
) {
    let chart_parts = Layout::default()
        .direction(Direction::Vertical)
        .constraints([Constraint::Min(3), Constraint::Length(2)])
        .split(area);
    let max_generation = chart_generation_max(&state.history).max(state.generation.max(1));
    type ScoreSeries = (String, Vec<(f64, f64)>, Color);
    let mut series: Vec<ScoreSeries> = Vec::new();
    let best = state
        .history
        .iter()
        .map(|point| {
            (
                point.generation as f64,
                point.best_feasible_score.unwrap_or(0.0),
            )
        })
        .collect();
    let mean = state
        .history
        .iter()
        .map(|point| {
            (
                point.generation as f64,
                point.mean_feasible_score.unwrap_or(0.0),
            )
        })
        .collect();
    series.push(("BEST FEASIBLE".into(), best, Color::Green));
    series.push(("FEASIBLE MEAN".into(), mean, Color::Cyan));
    let colors = [
        Color::Yellow,
        Color::Blue,
        Color::LightGreen,
        Color::LightYellow,
        Color::LightBlue,
    ];
    let ids = chart_candidate_ids(&state.history, &state.candidates, selected);
    for (index, id) in ids.iter().take(MAX_CHART_CANDIDATES).enumerate() {
        let points = state
            .history
            .iter()
            .filter_map(|point| {
                point
                    .top10
                    .iter()
                    .find(|candidate| candidate.candidate_id == *id)
                    .and_then(|candidate| {
                        candidate
                            .score
                            .map(|score| (point.generation as f64, score))
                    })
            })
            .collect();
        let rank = state
            .candidates
            .iter()
            .find(|candidate| candidate.candidate_id == *id)
            .and_then(|candidate| candidate.current_rank)
            .map(|rank| rank.to_string())
            .unwrap_or_else(|| "—".into());
        let color = if selected == Some(id.as_str()) {
            Color::Magenta
        } else {
            colors[index]
        };
        series.push((format!("{} r{}", short_id(id), rank), points, color));
    }
    let current_marker = state.generation as f64;
    series.push((
        "CURRENT GEN".into(),
        vec![(current_marker, 0.0), (current_marker, 1.0)],
        Color::DarkGray,
    ));
    let datasets = series
        .iter()
        .map(|(label, points, color)| {
            let modifier = if label == "BEST FEASIBLE" {
                Modifier::BOLD
            } else {
                Modifier::empty()
            };
            Dataset::default()
                .name(label.clone())
                .marker(symbols::Marker::Braille)
                .style(Style::default().fg(*color).add_modifier(modifier))
                .graph_type(GraphType::Line)
                .data(points)
        })
        .collect::<Vec<_>>();
    let chart = Chart::new(datasets)
        .x_axis(
            Axis::default()
                .title("generation")
                .bounds([0.0, max_generation as f64])
                .labels(vec![
                    Line::from("0"),
                    Line::from(max_generation.to_string()),
                ]),
        )
        .y_axis(
            Axis::default()
                .title("score")
                .bounds([0.0, 1.0])
                .labels(vec![
                    Line::from("0.0"),
                    Line::from("0.5"),
                    Line::from("1.0"),
                ]),
        )
        .block(panel_block(format!(
            "LIVE SCORE HISTORY — CURRENT GEN {}",
            state.generation
        )));
    frame.render_widget(chart, chart_parts[0]);

    let mut legend = vec![
        Span::styled(
            "LEGEND ",
            Style::default()
                .fg(Color::Gray)
                .add_modifier(Modifier::BOLD),
        ),
        Span::styled("● best feasible ", Style::default().fg(Color::Green)),
        Span::styled("● feasible mean", Style::default().fg(Color::Cyan)),
    ];
    for id in ids.iter().take(MAX_CHART_CANDIDATES) {
        let rank = state
            .candidates
            .iter()
            .find(|candidate| candidate.candidate_id == *id)
            .and_then(|candidate| candidate.current_rank)
            .map(|rank| rank.to_string())
            .unwrap_or_else(|| "—".into());
        legend.push(Span::styled(
            format!("  ● {} r{}", short_id(id), rank),
            Style::default().fg(if selected == Some(id.as_str()) {
                Color::Magenta
            } else {
                colors[ids
                    .iter()
                    .position(|candidate| candidate == id)
                    .unwrap_or(0)]
            }),
        ));
    }
    frame.render_widget(
        Paragraph::new(Line::from(legend))
            .style(Style::default().bg(Color::Rgb(15, 29, 48)))
            .wrap(Wrap { trim: true }),
        chart_parts[1],
    );
}

fn chart_candidate_ids(
    history: &[ScoreHistory],
    candidates: &[RankedCandidate],
    selected: Option<&str>,
) -> Vec<String> {
    let mut all_ids = BTreeSet::new();
    for point in history {
        for candidate in &point.top10 {
            all_ids.insert(candidate.candidate_id.clone());
        }
    }
    let mut ids = Vec::new();
    if let Some(selected) = selected {
        if all_ids.contains(selected) || candidates.iter().any(|c| c.candidate_id == selected) {
            ids.push(selected.to_string());
        }
    }
    let chosen_ids = ids.clone();
    ids.extend(
        all_ids
            .into_iter()
            .filter(|id| !chosen_ids.iter().any(|chosen| chosen == id))
            .take(MAX_CHART_CANDIDATES.saturating_sub(ids.len())),
    );
    ids
}

fn chart_generation_max(history: &[ScoreHistory]) -> u32 {
    history
        .last()
        .map(|point| point.generation)
        .unwrap_or(0)
        .max(1)
}

fn draw_ranking_table(
    frame: &mut ratatui::Frame<'_>,
    area: Rect,
    state: &DashboardState,
    selected: Option<&str>,
) {
    let candidates = state
        .candidates
        .iter()
        .take(TOP_CANDIDATES)
        .collect::<Vec<_>>();
    let short_ids = short_ids(
        candidates
            .iter()
            .map(|candidate| candidate.candidate_id.as_str()),
    );
    let rows = candidates.iter().enumerate().map(|(row_index, candidate)| {
        let index = candidate.current_rank.unwrap_or(99);
        let row_style = if !candidate.feasible {
            Style::default()
                .fg(Color::LightRed)
                .add_modifier(Modifier::BOLD)
        } else if index == 1 {
            Style::default()
                .fg(Color::LightGreen)
                .add_modifier(Modifier::BOLD)
        } else if candidate.pareto_rank == Some(0) {
            Style::default()
                .fg(Color::LightCyan)
                .add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(Color::LightYellow)
        };
        let selected_style = if selected == Some(candidate.candidate_id.as_str()) {
            row_style.bg(Color::Rgb(112, 35, 104)).fg(Color::White)
        } else {
            row_style
        };
        Row::new(vec![
            Cell::from(short_ids[row_index].clone()),
            Cell::from(
                candidate
                    .current_rank
                    .map(|x| x.to_string())
                    .unwrap_or_else(|| "—".into()),
            ),
            Cell::from(format!(
                "{} {}",
                candidate.movement,
                candidate
                    .rank_delta
                    .map(|x| format!("{x:+}"))
                    .unwrap_or_else(|| "—".into())
            )),
            Cell::from(
                candidate
                    .moo_display_score
                    .map(|x| format!("{x:.3}"))
                    .unwrap_or_else(|| "—".into()),
            ),
            Cell::from(if candidate.feasible { "PASS" } else { "FAIL" }),
            Cell::from(if candidate.mutation_id.is_some() {
                "MUTATION"
            } else {
                "SURVIVOR"
            }),
        ])
        .style(selected_style)
    });
    let table = Table::new(
        rows,
        [
            Constraint::Length(12),
            Constraint::Length(6),
            Constraint::Length(6),
            Constraint::Length(7),
            Constraint::Length(6),
            Constraint::Length(8),
        ],
    )
    .header(Row::new(vec![
        "CANDIDATE",
        "RANK",
        "MOVE",
        "SCORE",
        "GATE",
        "MARKER",
    ]))
    .block(panel_block(if state.phase.starts_with("SCORING") {
        format!(
            "{} · {}/{}",
            phase_label(&state.phase),
            state.scoring_completed,
            state.scoring_total
        )
    } else if state.candidates.is_empty() {
        "TOP 10 CANDIDATES · showing 0 of 10".into()
    } else {
        format!(
            "RANKED · TOP 10 · showing {} of 10{}",
            candidates.len(),
            if candidates.len() > visible_table_rows(area) {
                " · clipped"
            } else {
                ""
            }
        )
    }));
    let selected_index = state
        .candidates
        .iter()
        .take(TOP_CANDIDATES)
        .position(|candidate| Some(candidate.candidate_id.as_str()) == selected);
    let offset = selected_index
        .map(|index| index.saturating_sub(visible_table_rows(area).saturating_sub(1)))
        .unwrap_or(0)
        .min(candidates.len().saturating_sub(visible_table_rows(area)));
    let mut table_state = TableState::default()
        .with_offset(offset)
        .with_selected(selected_index);
    frame.render_stateful_widget(table, area, &mut table_state);
}

fn visible_table_rows(area: Rect) -> usize {
    area.height.saturating_sub(4).max(1) as usize
}

fn draw_candidate_context(
    frame: &mut ratatui::Frame<'_>,
    area: Rect,
    state: &DashboardState,
    selected: Option<&str>,
) {
    let Some(candidate) = selected
        .and_then(|id| state.candidates.iter().find(|c| c.candidate_id == id))
        .or_else(|| state.candidates.first())
    else {
        frame.render_widget(
            Paragraph::new("No candidate selected").block(
                Block::default()
                    .borders(Borders::ALL)
                    .title("SELECTED CANDIDATE"),
            ),
            area,
        );
        return;
    };
    let mut lines = vec![
        Line::from(Span::styled(
            format!("ID {}", candidate.candidate_id),
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        )),
        Line::from(Span::styled(
            "Press Enter for full candidate detail",
            Style::default().fg(Color::Gray),
        )),
        Line::from(format!(
            "RANKING  rank {} {}  score {}",
            candidate
                .current_rank
                .map(|x| x.to_string())
                .unwrap_or_else(|| "—".into()),
            candidate.movement,
            format_score(candidate.moo_display_score)
        )),
        Line::from(format!(
            "OBJECTIVES  role-fit {}  novelty {}",
            objective_value(candidate, "role_fit"),
            objective_value(candidate, "novelty_score")
        )),
    ];
    for id in [
        "eew",
        "ahew",
        "max_similarity",
        "novelty_band",
        "design_gate_status",
    ] {
        if let Some(value) = kpi_value(candidate, id) {
            lines.push(Line::from(value));
        }
    }
    frame.render_widget(
        Paragraph::new(lines)
            .style(Style::default().fg(Color::Gray))
            .block(panel_block("SELECTED CANDIDATE"))
            .wrap(Wrap { trim: true }),
        area,
    );
}

fn draw_candidate_modal(
    frame: &mut ratatui::Frame<'_>,
    screen: Rect,
    state: &DashboardState,
    candidate: &RankedCandidate,
) {
    let area = centered_rect(82, 88, screen);
    frame.render_widget(Clear, area);
    let mut lines = vec![
        Line::from(Span::styled(
            "CHEMICAL INSPECTION",
            Style::default()
                .fg(Color::Cyan)
                .add_modifier(Modifier::BOLD),
        )),
        Line::from(Span::styled(
            format!("IDENTITY  full candidate ID: {}", candidate.candidate_id),
            Style::default().fg(Color::Cyan),
        )),
        Line::from(Span::styled(
            format!(
                "LINEAGE  parents={} generation={} mutation={}",
                candidate.parent_ids.join(","),
                candidate.generation,
                candidate.mutation_id.as_deref().unwrap_or("none")
            ),
            Style::default().fg(Color::Gray),
        )),
        Line::from(Span::styled(
            format!(
                "RANKING  score {} rank {} {}",
                format_score(candidate.moo_display_score),
                candidate
                    .current_rank
                    .map(|x| x.to_string())
                    .unwrap_or_else(|| "—".into()),
                candidate.movement
            ),
            Style::default().fg(Color::Green),
        )),
        Line::from(format!(
            "OBJECTIVES  role-fit {}  novelty {}",
            objective_value(candidate, "role_fit"),
            objective_value(candidate, "novelty_score")
        )),
        Line::from(format!(
            "GATE STATUS  {}  failed modules {}",
            if candidate.feasible { "PASS" } else { "FAIL" },
            candidate.failed_modules
        )),
        Line::from(format!(
            "CHEMICAL ROLE  {}",
            candidate
                .chemical_preview
                .as_ref()
                .map(|p| p.role.as_str())
                .unwrap_or("unknown")
        )),
    ];
    for id in [
        "max_similarity",
        "novelty_band",
        "design_gate_status",
        "design_gate_reason",
        "eew",
        "ahew",
    ] {
        if let Some(value) = kpi_value(candidate, id) {
            lines.push(Line::from(value));
        }
    }
    if let Some(preview) = &candidate.chemical_preview {
        lines.push(Line::from(format!(
            "PREVIEW  {} — {}",
            preview.name, preview.render_status
        )));
        lines.extend(preview.ascii_lines.iter().cloned().map(Line::from));
        lines.push(Line::from(format!("SMILES  {}", preview.canonical_smiles)));
    } else {
        lines.push(Line::from("PREVIEW  unavailable"));
    }
    lines.push(Line::from(Span::styled(
        "Esc close  •  Up/Down select  •  q quit",
        Style::default().fg(Color::Gray),
    )));
    frame.render_widget(
        Paragraph::new(lines)
            .style(Style::default().fg(Color::Gray))
            .block(panel_block(format!(
                "CANDIDATE DETAIL — GEN {}",
                state.generation
            )))
            .wrap(Wrap { trim: true }),
        area,
    );
}

fn centered_rect(percent_x: u16, percent_y: u16, area: Rect) -> Rect {
    let horizontal = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage((100 - percent_x) / 2),
            Constraint::Percentage(percent_x),
            Constraint::Percentage((100 - percent_x) / 2),
        ])
        .split(area);
    Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage((100 - percent_y) / 2),
            Constraint::Percentage(percent_y),
            Constraint::Percentage((100 - percent_y) / 2),
        ])
        .split(horizontal[1])[1]
}

fn short_id(id: &str) -> String {
    let chars = id.chars().collect::<Vec<_>>();
    if chars.len() <= 10 {
        return id.to_string();
    }
    format!(
        "{}…{}",
        chars.iter().take(5).collect::<String>(),
        chars
            .iter()
            .rev()
            .take(4)
            .collect::<Vec<_>>()
            .into_iter()
            .rev()
            .collect::<String>()
    )
}

fn short_ids<'a>(ids: impl IntoIterator<Item = &'a str>) -> Vec<String> {
    let mut output: Vec<String> = Vec::new();
    for id in ids {
        let base = short_id(id);
        let mut display = base.clone();
        let mut width = 4;
        while output.iter().any(|existing| existing == &display) {
            if width > 16 {
                let marker = format!("{}#", base);
                let occurrence = output
                    .iter()
                    .filter(|existing| *existing == &base || existing.starts_with(&marker))
                    .count()
                    + 1;
                display = format!("{}#{}", base, occurrence);
                break;
            }
            display = format!(
                "{}…{}",
                id.chars().take(4).collect::<String>(),
                stable_id_suffix(id, width)
            );
            width += 2;
        }
        output.push(display);
    }
    output
}

fn stable_id_suffix(id: &str, width: usize) -> String {
    let mut hash = 0xcbf29ce484222325u64;
    for byte in id.as_bytes() {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    format!("{hash:016x}")[..width.min(16)].to_string()
}

fn compact_json(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::String(value) => value.clone(),
        other => other.to_string(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use amphora_core::{
        apply_rank_deltas, make_score_history, ChemicalPreview, HistoryCandidate, ObjectiveRow,
    };

    fn candidate(id: &str, rank: usize, score: f64) -> RankedCandidate {
        RankedCandidate {
            candidate_id: id.into(),
            current_rank: Some(rank),
            previous_rank: None,
            rank_delta: None,
            movement: "—".into(),
            feasible: true,
            ranked: true,
            pareto_rank: Some(0),
            moo_display_score: Some(score),
            eligible_objectives: 2,
            failed_modules: 0,
            objective_rows: vec![ObjectiveRow {
                id: "novelty_score".into(),
                module_id: "novelty".into(),
                path: "novelty_score".into(),
                value: score,
                direction: "maximize".into(),
                unit: "normalized_0_1".into(),
                eligible: true,
                pareto_rank: Some(0),
                normalized_value: Some(score),
            }],
            claim_locks: Default::default(),
            display_kpis: vec![],
            mutation_id: None,
            parent_ids: vec![],
            generation: 0,
            chemical_preview: None,
        }
    }

    #[test]
    fn rank_delta_and_history_are_deterministic() {
        let previous = vec![candidate("a", 1, 0.8), candidate("b", 2, 0.7)];
        let mut current = vec![candidate("b", 1, 0.9), candidate("a", 2, 0.6)];
        apply_rank_deltas(&mut current, Some(&previous));
        assert_eq!(current[0].movement, "↑");
        assert_eq!(current[0].rank_delta, Some(1));
        let history = make_score_history(1, &current, 5);
        assert_eq!(history.generation, 1);
        assert_eq!(history.best_feasible_score, Some(0.9));
        assert_eq!(history.top10[0].candidate_id, "b");
    }

    #[test]
    fn preview_serializes_without_ansi() {
        let candidate = candidate("a", 1, 0.8);
        let state = DashboardState {
            run_id: "run".into(),
            generation: 0,
            generations: 1,
            phase: "RANKED".into(),
            scoring_completed: 0,
            scoring_total: 0,
            rejected_candidates: 0,
            worker_failures: 0,
            elapsed_ms: 0,
            throughput: Throughput::default(),
            active_workers: 1,
            registered_modules: 0,
            active_modules: 0,
            modules: vec![],
            candidates: vec![candidate],
            history: vec![],
            selected_candidate: Some("a".into()),
            paused: false,
            objective_ready: true,
            finished: false,
            logs: vec![],
        };
        assert!(!state_text(&state).contains('\u{1b}'));
    }

    #[test]
    fn selection_moves_and_modal_can_pin_the_selected_candidate() {
        let mut first = candidate("a", 1, 0.8);
        first.chemical_preview = Some(ChemicalPreview {
            canonical_smiles: "C".into(),
            role: "resin".into(),
            name: "methane".into(),
            ascii_lines: vec!["⠿".into()],
            render_status: "BRAILLE".into(),
        });
        let state = DashboardState {
            run_id: "run".into(),
            generation: 0,
            generations: 1,
            phase: "RANKED".into(),
            scoring_completed: 0,
            scoring_total: 0,
            rejected_candidates: 0,
            worker_failures: 0,
            elapsed_ms: 0,
            throughput: Throughput::default(),
            active_workers: 1,
            registered_modules: 0,
            active_modules: 0,
            modules: vec![],
            candidates: vec![first, candidate("b", 2, 0.7)],
            history: vec![],
            selected_candidate: None,
            paused: false,
            objective_ready: true,
            finished: false,
            logs: vec![],
        };
        let mut app = DashboardApp::new();
        app.update(state);
        assert_eq!(app.selected.as_deref(), Some("a"));
        app.move_selection(1);
        assert_eq!(app.selected.as_deref(), Some("b"));
        app.modal_open = true;
        assert!(app.modal_open);
        app.modal_open = false;
        assert!(!app.modal_open);
    }

    #[test]
    fn empty_history_uses_fixed_chart_bounds() {
        assert_eq!(chart_generation_max(&[]), 1);
        assert_eq!(
            chart_generation_max(&[ScoreHistory {
                generation: 0,
                best_feasible_score: None,
                mean_feasible_score: None,
                feasible_count: 0,
                ranked_count: 0,
                top10: vec![]
            }]),
            1
        );
    }

    #[test]
    fn initial_scoring_state_is_explicit_in_headless_text() {
        let state = DashboardState {
            run_id: "run".into(),
            generation: 0,
            generations: 10,
            phase: "SCORING_INITIAL_POPULATION".into(),
            scoring_completed: 4,
            scoring_total: 20,
            rejected_candidates: 1,
            worker_failures: 0,
            elapsed_ms: 0,
            throughput: Throughput::default(),
            active_workers: 20,
            registered_modules: 4,
            active_modules: 4,
            modules: vec![],
            candidates: vec![],
            history: vec![],
            selected_candidate: None,
            paused: false,
            objective_ready: false,
            finished: false,
            logs: vec![],
        };
        let text = state_text(&state);
        assert!(text.contains("SCORING INITIAL POPULATION — 4/20"));
        assert!(text.contains("rejected 1"));
        assert!(!text.contains("UNRANKED"));
    }

    #[test]
    fn short_ids_are_readable_and_unique_for_colliding_endpoints() {
        let ids = short_ids([
            "DGEBA-long-middle-a-md4c",
            "DGEBA-different-middle-b-md4c",
            "DGEBA-long-middle-a-md4c",
        ]);
        assert_eq!(short_id("DGEBA-long-candidate-md4c"), "DGEBA…md4c");
        assert_eq!(ids.len(), 3);
        assert_ne!(ids[0], ids[1]);
        assert_ne!(ids[0], ids[2]);
        assert_ne!(ids[1], ids[2]);
    }

    #[test]
    fn chart_keeps_selected_candidate_inside_the_five_series() {
        let history = vec![ScoreHistory {
            generation: 0,
            best_feasible_score: Some(0.9),
            mean_feasible_score: Some(0.5),
            feasible_count: 10,
            ranked_count: 10,
            top10: (0..10)
                .map(|index| HistoryCandidate {
                    candidate_id: format!("candidate-{index}"),
                    score: Some(index as f64 / 10.0),
                    pareto_rank: Some(0),
                    current_rank: Some(index + 1),
                    previous_rank: None,
                    rank_delta: None,
                    movement: "—".into(),
                })
                .collect(),
        }];
        let candidates = vec![candidate("candidate-9", 10, 0.1)];
        let ids = chart_candidate_ids(&history, &candidates, Some("candidate-9"));
        assert_eq!(ids.len(), 5);
        assert_eq!(ids[0], "candidate-9");
    }

    #[test]
    fn selection_navigates_the_visible_top_ten() {
        let candidates = (0..10)
            .map(|index| {
                candidate(
                    &format!("candidate-{index}"),
                    index + 1,
                    1.0 - index as f64 / 10.0,
                )
            })
            .collect();
        let state = DashboardState {
            run_id: "run".into(),
            generation: 0,
            generations: 1,
            phase: "RANKED".into(),
            scoring_completed: 10,
            scoring_total: 10,
            rejected_candidates: 0,
            worker_failures: 0,
            elapsed_ms: 0,
            throughput: Throughput::default(),
            active_workers: 1,
            registered_modules: 0,
            active_modules: 0,
            modules: vec![],
            candidates,
            history: vec![],
            selected_candidate: Some("candidate-0".into()),
            paused: false,
            objective_ready: true,
            finished: false,
            logs: vec![],
        };
        let mut app = DashboardApp::new();
        app.update(state);
        for _ in 0..9 {
            app.move_selection(1);
        }
        assert_eq!(app.selected.as_deref(), Some("candidate-9"));
        app.move_selection(1);
        assert_eq!(app.selected.as_deref(), Some("candidate-0"));
    }

    #[test]
    fn chemical_preview_round_trips_as_typed_state() {
        let preview = ChemicalPreview {
            canonical_smiles: "CC".into(),
            role: "hardener".into(),
            name: "ethane".into(),
            ascii_lines: vec!["⠿".into()],
            render_status: "BRAILLE".into(),
        };
        let encoded = serde_json::to_string(&preview).unwrap();
        assert_eq!(
            serde_json::from_str::<ChemicalPreview>(&encoded).unwrap(),
            preview
        );
    }
}
