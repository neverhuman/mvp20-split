//! amphora-solver-lab: a genuine constrained formulation optimizer whose
//! AUTHORITY is bounded (AUDIT_ONLY), not its capability.
//!
//! Capability real, authority AUDIT_ONLY, promotion requires human ceremony.
//!
//! - Oracles read EXCLUSIVELY from already-signed KPI/receipt JSON in the
//!   tree, sha256-pinned; tampered sources are refused (fail-closed).
//! - Search: exhaustive DoE enumeration, projected-gradient continuous blend
//!   optimization over the composition simplex, and NSGA-II with a pinned
//!   seed and deterministic tournament.
//! - Determinism by construction: f64 only, ordered reductions, BTreeMap
//!   (never HashMap) on result paths, pinned seeds; every demo diagnostic is
//!   two-replay byte-stable.
//! - Every output carries authority: "AUDIT_ONLY" and claim locks
//!   (promotes_authority: false, modifies_manifest: false) and is DSSE-signed
//!   by benchmarks/sign_solver_lab_demos.py.

pub mod demos;
pub mod doe;
pub mod nsga2;
pub mod oracle;
pub mod simplex;
