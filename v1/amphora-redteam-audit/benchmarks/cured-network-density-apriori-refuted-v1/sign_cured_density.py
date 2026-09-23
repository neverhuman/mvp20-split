"""DSSE-Ed25519 sign the cured-network a-priori density REFUTATION audit.
Signs the canonical diagnostic whose bytes reproduced identically across two
independent runs (two-replay SHA gate = PASS). Signs with the repo
LOCAL_DEVELOPMENT_AUDIT_ONLY key (local-*), explicitly NOT trust-anchored.
AUDIT_ONLY: promotes nothing, signs no phase0 receipt, modifies no existing
receipt or the master manifest (stays 66/11)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

BENCH = Path("amphora-redteam-audit/benchmarks/cured-network-density-apriori-refuted-v1")
KEY = Path(".amphora/control/local-ed25519.key")
PUB = json.loads(Path(".amphora/control/local-ed25519.pub.json").read_text())
CANONICAL_SHA = "9ff17c8bc8fca43c272744311d5ea4cd36a7071d0a6391aca735a25b4f1cda00"

def sha(b): return hashlib.sha256(b).hexdigest()
def pae(t, body): return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body

diag_bytes = (BENCH / "diagnostic.canonical.json").read_bytes()
runb_bytes = (BENCH / "diagnostic.runB.json").read_bytes()
assert sha(diag_bytes) == CANONICAL_SHA, sha(diag_bytes)
assert sha(runb_bytes) == CANONICAL_SHA, "two-replay gate FAILED"
diag = json.loads(diag_bytes)
harness_sha = sha((BENCH / "cured_density_audit.py").read_bytes())

receipt = {
    "schema": "amphora.redteam-audit.cured-network-density-apriori-refuted-v1-replay-receipt.v1",
    "authority": "AUDIT_ONLY",
    "run_type": "CURED_NETWORK_DENSITY_APRIORI_REFUTATION_REDTEAM",
    "promotes_authority": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "module": "amphora-redteam-audit",
    "benchmark": "amphora-redteam-audit/cured-network-density-apriori-refuted-v1",
    "target_module": diag["target_module"],
    "target_capability": diag["target_capability"],
    "purpose": (
        "Red-team test of the HIGHEST-VALUE achievable-looking un-attempted cured-network "
        "axis: an a-priori, structure-only mass density of the cured DGEBA+amine network "
        "(foundational to free-volume -> water/O2 permeability -> the anti-corrosion "
        "BARRIER function). The predictor reuses the portfolio's OWN density-validated "
        "Fedors/Van-Krevelen molar-volume engine (validated vs BigSolDB solvent densities) "
        "applied to the fully-reacted stoichiometric network unit (epoxy + N-H -> "
        "beta-hydroxyamine, atoms conserved). VERDICT: REFUTED. The naive additive route "
        "over-predicts the one rights-clean CC-BY measured network density (DGEBA+IPDA: "
        "1.33 pred vs 1.105 measured, +20.5%) for three independently-evidenced reasons. "
        "Tested BEFORE any claim so a future run cannot oversell this predictor."),
    "non_circularity": diag["non_circularity"],
    "kpis": diag["kpis"],
    "gates": diag["gates"],
    "verdict": diag["verdict"],
    "reaction_delta_selfcheck": diag["reaction_delta_selfcheck"],
    "diagnostics_summary": {
        "cause_1_additive_engine_overpredicts_clustered_polyols": {
            "glycerol_pct": diag["kpis"]["engine_overprediction_glycerol_pct"],
            "triethanolamine_pct": diag["kpis"]["engine_overprediction_triethanolamine_pct"],
            "note": "the cured network IS a poly-beta-hydroxyamine -> worst case for additive V"},
        "cause_2_reaction_diff_overshoots_cure_shrinkage": diag["cure_shrinkage_sanity"],
        "cause_3_motif_correction_does_not_transfer": diag["exploratory_motif_correction"]},
    "rights_discipline": {
        "scored_only_rights_clean_CCBY": diag["rights_clean_source"],
        "rejected_rights_restricted": diag["corroboration_rights_restricted_NOT_SCORED"],
        "statement": "Scored on exactly ONE rights-clean CC-BY-4.0 measured network density "
            "(DGEBA+IPDA 1.105, 10.3390/polym13081348). The richer multi-amine experimental "
            "set (DETA/IPDA/MXDA, ACS Omega 10.1021/acsomega.2c03071) is CC-BY-NC-ND and was "
            "REJECTED on rights -- carried ONLY as non-scored corroboration. This re-confirms "
            "the cured-network DATA-RIGHTS wall for density specifically, this run."},
    "honest_limitations": diag["honest_limitations"],
    "red_team_findings_this_run": [
        "UPHELD THE FOUNDER (re-verified LIVE this run): module-manifest.json lists all 29 "
        "modules scientific_readiness=UNVALIDATED (0 VALIDATED); config/program/"
        "phase0-decision-report.v2.json status=EXECUTION_INCOMPLETE with promotable=false for "
        "every module. 'FULL Phase-0' is a GOVERNANCE milestone, NOT validated science.",
        "The obvious a-priori cured-network density predictor is REFUTED (+20.5% on the one "
        "rights-clean anchor). This is a NEGATIVE result, recorded so it cannot be mistaken "
        "for progress: the additive Fedors/VK engine does not transfer from solvents/liquids "
        "to the clustered-H-bond, low-cure-shrinkage cured epoxy-amine network.",
        "Reaction-delta bookkeeping independently verified EXACT vs direct RDKit decomposition "
        "for both the primary->secondary (333.8) and primary->tertiary (255.5) transitions -- "
        "the refutation is a real physics/parameterization limit, not an arithmetic bug.",
        "A motif correction calibrated NON-CIRCULARLY on 10 independent aminoalcohol/polyol "
        "CRC densities (c=2.634 cm3/motif, cal RMS 3.5%) FAILS to transfer to the network "
        "(residual +17.6%): the correction is diluted in the large aromatic/ether repeat unit.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "replays": 2, "independent_runs": True,
        "code_path_independence": "single Python harness, two independent executions (honest scope)",
        "canonical_diagnostic_sha256": CANONICAL_SHA,
        "runB_diagnostic_sha256": sha(runb_bytes),
        "harness_sha256": harness_sha,
    },
    "honest_forward_path": [
        "This refutes the NAIVE additive-volume route only. A proper amorphous-network "
        "density method (Van Krevelen amorphous V = V_w x 1.6, or Bicerano network group "
        "correlation with an explicit crosslink-densification term) is the next candidate.",
        "To VALIDATE any cured-network density predictor to a PHASE_0 standard requires >=4 "
        "rights-clean CC-BY-4.0 DGEBA+amine cured densities spanning aliphatic/cycloaliphatic/"
        "aromatic amine classes (only 1 is currently in reach). Acquiring these through "
        "amphora-source-ledger with signed rights receipts is the founder-actionable blocker.",
    ],
    "does_not_close": [
        "does NOT promote amphora-molecule-property (or any module) to PHASE_0 or change any "
        "scientific_readiness (live: all 29 UNVALIDATED, 0 VALIDATED)",
        "does NOT add any PHASE_0 module; 'FULL Phase-0' remains a governance milestone",
        "does NOT modify any of the 66 signed receipts or the receipts manifest (66/11)",
        "does NOT claim a validated density predictor -- this receipt records a REFUTATION",
        "does NOT score on any rights-restricted (CC-BY-NC / -ND) datum",
        "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing (AUDIT_ONLY key)",
    ],
    "does_not": diag["does_not"],
    "signing_key": {"key_id": PUB["key_id"], "authority": PUB["authority"],
                    "trust_anchored_in_phase0_store": False},
}
body = json.dumps(receipt, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.redteam-cured-network-density-apriori-refuted+json"
sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
sig = sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}]}
out = BENCH / "replay_receipt.v1.dsse.json"
out.write_text(json.dumps(envelope, indent=2, sort_keys=True))
print("WROTE", out)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
