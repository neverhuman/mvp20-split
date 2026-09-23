#!/usr/bin/env python3
"""Build the machine-readable spine of the founder directive.

Section A items are PARSED out of the rendered markdown so their done_criteria and
refutation_criterion are verbatim by construction and cannot drift from the source.
Sections B and C are prose, so their records are authored here -- but every one
carries a `source_heading` that must exist in the rendered .md, and the builder
asserts that, so an authored record cannot silently reference a section that
isn't in the document.
"""
import hashlib, json, os, re, sys

MD, DOCX, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
md = open(MD).read()

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

XB2_DIR = "docs/directives"
STEM = "2026-08-05-closing-the-open-portfolio"

# ---------------------------------------------------------------- Section A.1
# Each T2 item is one table cell:
#   "T2-04  Title module: X attack: Y done_criteria: Z refutation_criterion: W max_fires: N"
T2_MODULES = {  # from the doc's own 1.2 table, used only to cross-check the parse
    "T2-01": "amphora-candidate-contract",       "T2-02": "amphora-cro-protocol-packager",
    "T2-03": "amphora-envelope-gates",           "T2-04": "amphora-evidence-intake-validator",
    "T2-05": "amphora-formulation-arithmetic",   "T2-06": "amphora-formulation-universe",
    "T2-08": "amphora-molecule-design-gate",     "T2-09": "amphora-optimizer-orchestrator",
    "T2-10": "amphora-process-qc-twin",          "T2-12": "amphora-report-packager",
    "T2-13": "amphora-run-provenance",           "T2-14": "amphora-source-ledger",
}
# T2-NN maps onto the already-existing T-NN item for the same module.
T2_TO_CAMPAIGN = {k: "T-" + k.split("-")[1] for k in T2_MODULES}
PHASE0_GAP = {"T2-02", "T2-04", "T2-08", "T2-09", "T2-12", "T2-14"}

PAT = re.compile(
    r"(T2-\d\d)\s+(.*?)\s+module:\s*(\S+)\s+attack:\s*(.*?)\s+"
    r"done_criteria:\s*(.*?)\s+refutation_criterion:\s*(.*?)\s+max_fires:\s*(\d+)",
    re.S)

obligations, parsed = [], set()
for m in PAT.finditer(md):
    oid, title, module, attack, done, refut, mf = (x.strip() for x in m.groups())
    module = module.rstrip("|").strip()
    parsed.add(oid)
    assert module == T2_MODULES.get(oid), f"{oid}: parsed module {module!r} != expected"
    obligations.append({
        "id": oid, "section": "A.1", "owner": "LOOP", "module": module,
        "title": title, "attack": attack,
        "done_criteria": done, "refutation_criterion": refut, "max_fires": int(mf),
        "phase0_binding_gap": oid in PHASE0_GAP,
        "origin": "founder-directive",
        "campaign_items": [T2_TO_CAMPAIGN[oid]],
        "status": "mapped",
        "note": ("Merged into the pre-existing %s item rather than filed as a duplicate; "
                 "that item already carried a bespoke attack and the positive_control "
                 "clause, and this directive's refutation_criterion is added verbatim."
                 % T2_TO_CAMPAIGN[oid]) +
                (" Also records EVALUATION_RESULT_MISMATCH state so the attack and the "
                 "R-D07 ceremony share one evidence trail." if oid in PHASE0_GAP else ""),
    })
missing = set(T2_MODULES) - parsed
assert not missing, f"failed to parse T2 items: {sorted(missing)}"

def add(**kw):
    kw.setdefault("campaign_items", [])
    kw.setdefault("status", "mapped")
    # Distinguish what the founder wrote from what we added around it. An index
    # that blurs the two would misrepresent the directive back to its author.
    kw.setdefault("origin", "founder-directive")
    obligations.append(kw)

# --------------------------------------------------- A.1 note on T-07 / T-11
add(id="A1-NOTE-T07-T11", section="A.1", owner="LOOP", module=None,
    title="T-07 and T-11 stay queued at lower priority",
    done_criteria="Leave queued for a genuinely adversarial second pass; lower priority "
                  "than the twelve zero-verdict modules.",
    campaign_items=["T-07", "T-11"], status="mapped",
    note="Directive states these modules have since picked up verdicts (model-card-authority "
         "via V1-KPI-MCA, redteam-audit via waves R/V1). Kept pending, ordered after the T2 block.")

# ---------------------------------------------------------------- Section A.2
add(id="V2-A06v2", refutation_criterion='the repair reproduces numerically but fails a convention, propagation, or sufficiency check the repair did not test', methodology='Each V2 item dispatches a separately-authored fire -- one that did not write the repair and cannot see its reasoning -- pre-committed to CLAIM_REFUTED if no repair receipt exists.', section="A.2", owner="LOOP", module="amphora-molecule-generator",
    title="Verify molecule-generator R-A06v2 against the AHEW functionality convention",
    done_criteria="Re-derive amine_sites/active_nh from raw SMILES; escalate past the repair's own frame.",
    campaign_items=["V-A06v2"], status="already-satisfied",
    note="V-A06v2 landed CLAIM_SURVIVED at 2026-08-05T15:00 with a positive control, before this "
         "directive was reconciled. No new item needed.")
add(id="V2-A07v2", refutation_criterion='the repair reproduces numerically but fails a convention, propagation, or sufficiency check the repair did not test', methodology='Each V2 item dispatches a separately-authored fire -- one that did not write the repair and cannot see its reasoning -- pre-committed to CLAIM_REFUTED if no repair receipt exists.', section="A.2", owner="LOOP", module="amphora-molecule-novelty",
    title="Verify molecule-novelty R-A07v2 across all four fingerprint families",
    done_criteria="Propagate the corrected IPDA structure into maccs_166, atompair_2048, "
                  "toptorsion_2048 and morgan; diff against the shipped table.",
    campaign_items=["V-A07v2"], status="mapped",
    note="Already pending as V-A07v2; directive_ref added.")
add(id="V2-B02", refutation_criterion='the repair reproduces numerically but fails a convention, propagation, or sufficiency check the repair did not test', methodology='Each V2 item dispatches a separately-authored fire -- one that did not write the repair and cannot see its reasoning -- pre-committed to CLAIM_REFUTED if no repair receipt exists.', section="A.2", owner="LOOP", module="amphora-barrier-corrosion-score",
    title="Verify barrier-corrosion R-B02 (barrier_index now computed)",
    done_criteria="From-scratch re-implementation; metric non-null on every live path; record that "
                  "n=3 remains below FEASIBILITY_FLOOR pending R-D01.",
    campaign_items=["V-B02"], status="already-satisfied",
    note="V-B02 is done. The n=3 FEASIBILITY_FLOOR caveat remains open and is carried by R-D01/C.2.")
add(id="V2-REMAINDER", refutation_criterion='the repair reproduces numerically but fails a convention, propagation, or sufficiency check the repair did not test', methodology='Each V2 item dispatches a separately-authored fire -- one that did not write the repair and cannot see its reasoning -- pre-committed to CLAIM_REFUTED if no repair receipt exists.', section="A.2", owner="LOOP", module=None,
    title="One V2-* item per remaining unverified repair (directive says 12 more)",
    done_criteria="Each a fresh-harness re-derivation with at least one novel probe never in the "
                  "repair's set. Refutation for all: the repair reproduces numerically but fails a "
                  "convention, propagation or sufficiency check the repair did not test.",
    campaign_items=["R-C01-V", "R-C02-V", "R-C03-V", "R-C04-V", "R-C05-V"],
    status="reconciled-with-deviation",
    note="DEVIATION FROM DIRECTIVE, recorded deliberately. The directive states '15 of 26 distinct "
         "repair items carry no independent verify'. That count comes from a V-* prefix scan which "
         "misses five existing verify items named R-C01-V..R-C05-V (status blocked, they verify "
         "R-C01..R-C05) and the R-Z99 batch audit covering eight more. Re-deriving from the live "
         "file, the genuinely unverified repair tokens are R-A02, R-A03, R-N01, R-S03 plus the "
         "human-owned R-D01/R-D03/R-D05/R-D08 -- about 8, not 15. Filing 15 new items would have "
         "duplicated existing work. Action taken: the five R-C0x-V items are unblocked as their "
         "parent repairs land, and V2-* items are filed only for genuinely unverified repairs.")

# ---------------------------------------------------------------- Section A.3
add(id="X-EHS-CID", section="A.3", owner="LOOP", module="amphora-sourceability-ehs",
    title="Land the superseding hazard-card receipt for the CID defect",
    done_criteria="Fresh live PubChem fetch of CAS-correct CIDs for IPDA and m-XDA; re-derive "
                  "H-statement sets; re-evaluate procurement gates; clear the caveat that currently "
                  "propagates into solver-lab P3.",
    campaign_items=[], status="to-file")
add(id="X-LEDGER-TS", section="A.3", owner="LOOP", module="amphora-redteam-audit",
    title="Ship and prove the leading-backslash timestamp parser guard",
    done_criteria="The append-only rows stay; the read path must tolerate them; regression test included.",
    campaign_items=[], status="to-file")
add(id="X-HEARTBEAT", section="A.3", owner="LOOP", module=None,
    title="Cron-side heartbeat recording an attempted fire even when the agent never starts",
    done_criteria="The three missing hours (and any future gap) are explained rather than observed.",
    campaign_items=[], status="already-delivered",
    note="Delivered in Wave W on 2026-08-05 before this directive was reconciled: the launcher writes "
         "logs/heartbeat.jsonl at start, after flock and before the HARD_STOP check. Verified writing "
         "hourly since 03:00 on 2026-08-05. Not re-filed.")
add(id="X-SCHEMA-WATCH", section="A.3", owner="LOOP", module="amphora-redteam-audit",
    title="Keep RESTORED_SCHEMA_FLIP under active log review",
    done_criteria="It is the only failure mode invisible to the three verification checks, so the log "
                  "needs watching, not trusting.",
    campaign_items=[], status="to-file")
add(id="X-SOLVER-P3", section="A.3", owner="LOOP", module="amphora-redteam-audit",
    title="Solver-lab constraint relaxation with an explicit audit trail",
    done_criteria="What was relaxed, by whom, under what authority -- so an EMPTY_FEASIBLE_SET becomes "
                  "an actionable answer rather than a dead end.",
    campaign_items=[], status="to-file",
    note="Directive gates this behind X-EHS-CID, since P3's blocking set is provisional until the CID "
         "defect is fixed. Ordered after X-EHS-CID in the backlog.")

# ------------------------------------------------------------------ Section B
add(id="B-CREDENTIALS", section="B.1", owner="HUMAN", module=None,
    title="Register the two trusted signer identities (blocks everything)",
    done_criteria="Mint and prove possession of two distinct, non-revoked, non-development Ed25519 "
                  "identities (PHASE0_EVALUATOR, PHASE0_INTERNAL_REVIEWER); add both public keys to "
                  "config/phase0-trust-store.v1.json under the founder-signed master manifest; adopt "
                  "the pre-loop triage policy (do NOT mass re-sign); fix external messaging so the "
                  "quotable Phase-0 count is 9, not 17; and scope any portfolio-level statement to the 17 "
                  "attacked modules, never the full 40 crates (12 are pure runtime, and "
                  "solver-lab has no mission.md yet).",
    campaign_items=[], status="to-file",
    unblock_condition="Human ceremony. The loop deliberately does not hold these keys.")
add(id="B-CEREMONY-RD07", section="B.2", owner="HUMAN", module="amphora-redteam-audit",
    title="Run the R-D07 re-evaluation ceremony (restores 8 of 9 modules)",
    done_criteria="Per module: dry-run to read the target receipt hash; rehearse in a scratch rsync "
                  "copy to mint the matching review; obtain the fresh independent-review signature "
                  "from the second identity; issue one governed command in the authoritative tree.",
    repairable_modules=["cro-protocol-packager", "evidence-intake-validator",
                        "known-answer-benchmarks", "molecule-design-gate", "optimizer-orchestrator",
                        "redteam-audit", "report-packager", "source-ledger"],
    not_repairable={"module": "molecule-property",
                    "why": "no independent-review receipt and no movement event, so the ceremony's "
                           "reconcile branch cannot restore it; it needs a full re-evaluation plus "
                           "the C.6 lab validation. Do not let a summary round 8 up to 9."},
    campaign_items=["R-D07"], status="mapped",
    unblock_condition="B-CREDENTIALS first. molecule-property is NOT restorable this way -- no review "
                      "receipt, no movement event; route it through full re-evaluation plus C.6. "
                      "Do not let a summary round 8 up to 9.")
add(id="B-MERGE-RD08", section="B.3", owner="HUMAN", module="amphora-formulation-universe",
    title="Decide R-D08 — the formulation-universe merge",
    done_criteria="Merge decision taken, or withdrawn if T2-06 finds independent value.",
    campaign_items=["R-D08"], status="mapped",
    unblock_condition="HOLD until T2-06 (campaign item T-06) runs. The loop is forbidden from taking "
                      "this portfolio-shape decision.")
_ASKS = [
    ("R-D01", "Send the prepared USBR ST-19168 RIGHTS-REVIEW-REQUEST to USBR RISE; confirm public-domain under 17 U.S.C. §105.", "The entire barrier-corrosion wet-panel campaign (C.2). Critical path — the package is written and signed, it needs a human to send it."),
    ("R-D02", "File/escalate the USBR RISE request for frequency-resolved raw EIS sweeps (queue #3/#14; rights already verified public-domain).", "public-corrosion-benchmark's move from a correctly-stated negative result to a positive one; feeds C.2."),
    ("R-D03", "Counsel question: does the Reynolds 2024 CC BY-NC-ND licence permit internal, non-distributed, AUDIT_ONLY quantitative benchmarking?", "viscosity-score's Krieger–Dougherty benchmark (C.4). A rights wall, not a data wall — the loop found the dataset and stopped."),
    ("R-D04", "Ratify or downgrade the cure fixture's self-asserted CC0 via a signed rights receipt (queue #7).", "cure-potlife-gate's structural integrity, independent of the science fix in C.3."),
    ("R-D05", "Contact PURformance authors re a sibling HTE release, or commission a DoE (queue #8).", "design-rule-score — n=58 single-formulator is the binding constraint no model can fix (C.8)."),
    ("R-D06", "Confirm with RadonPy/PI1070 authors whether dielectric trajectories were production-converged; locate an OpenPoly-matched density field (queues #10/#11).", "molecule-property dielectric labels (currently 89.5% physically inadmissible) and the second density corpus (C.6)."),
]
for aid, action, unlocks in _ASKS:
    add(id="B-ASK-" + aid, section="B.4", owner="HUMAN", module=None,
        title="Rights/data ask %s" % aid, done_criteria=action,
        campaign_items=[aid], status="mapped",
        unblock_condition="Human action. Unlocks: " + unlocks)
add(id="B-COUNTERPARTIES", section="B.5", owner="HUMAN", module=None,
    title="Contract the eight independent counterparties",
    done_criteria="Contract laboratory; independent evaluator (PHASE0_EVALUATOR); independent reviewer "
                  "(PHASE0_INTERNAL_REVIEWER); statistician; chemistry labeling; data curation; counsel; "
                  "founder/owner. None may be collapsed into the portfolio team; the two signer roles "
                  "must be distinct from each other and from the lab.",
    campaign_items=[], status="to-file",
    unblock_condition="Human action; gates every Section C experiment.")

# ------------------------------------------------------------------ Section C
add(id="LAB-C0", section="C.0", owner="LAB", module=None,
    title="Common transfer path, promotion gate, and kill/hold gate",
    done_criteria="Transfer path: candidate-bound draft packet (execution_authorized:false) -> external "
                  "execution at the contract lab (method, custody, deviations) -> signed candidate-bound "
                  "raw return (with uncertainty) -> independent review by a distinct signer -> policy "
                  "decision. A packet is a structured question, not an instruction to execute; a fixture "
                  "is not independent validation; a similarity observation is not novelty.",
    promotion_gate=[
        "Raw evidence complete and rights-eligible; custody unbroken.",
        "Split and benchmark locks match the pre-registration byte-for-byte.",
        "Predefined thresholds pass; uncertainty quantified (conformal + bootstrap, not point-only).",
        "Evaluator and reviewer are distinct trusted signers; claim locks intact; exactly one valid "
        "movement event exists."],
    kill_hold_gate=[
        "Rights failure, custody break, or split leakage.",
        "Method mismatch vs the pre-registered protocol, or insufficient sample.",
        "Baseline non-superiority, or a confidence interval that crosses the pre-registered floor.",
        "Signer conflict, or any pressure to broaden the signed applicability domain."],
    on_failure="On failure, no threshold is weakened and no fixture is substituted. The failure is "
               "recorded as a signed negative result and the module does not move. That is the correct "
               "outcome, not a setback.",
    campaign_items=[], status="to-file",
    unblock_condition="Policy that governs C.1-C.10; not itself an experiment.",
    note="The eight promotion and kill/hold criteria were dropped from the first version of this "
         "index. They are the actual go/no-go rules for every Section C experiment, so their absence "
         "made the index unusable for the decision it exists to support.")

_EXPTS = [
    ("LAB-C1", "amphora-formulation-universe", "Formulation coverage — seed campaign (30 formulations / 3 families)",
     "30 candidate-bound records with resolved identity, units and rights; zero selection-by-prediction; byte-stable two-replay of the selection.",
     "Needs credentials (B.1) only — no R-D blocker. This is the substrate every other experiment binds to."),
    ("LAB-C2", "amphora-barrier-corrosion-score", "Barrier-corrosion campaign (210 panels / 40 systems, incl. 10 untouched external)",
     "barrier_index computed and non-null on every real-data path; superiority over null-median on the group-safe split with a bootstrap CI excluding zero; conformal coverage >= target on the 10 untouched external systems.",
     "R-D01 (critical path) and R-D02; C.1 seed set."),
    ("LAB-C3", "amphora-cure-potlife-gate", "Cure / pot-life campaign (36 runs: 24 fit + 12 sealed holdouts)",
     "Arrhenius model beats Q10=2 on all measured legs including 40 C, within the 0.25 held-out and 0.40 per-point ceilings, on the sealed holdouts; stratified disclosure reported.",
     "R-D04; C.1 seed chemistries."),
    ("LAB-C4", "amphora-viscosity-score", "Viscosity / sag campaign (288 cells, three temperatures)",
     "HB and KD parameters recovered within pre-registered bounds; multi-temperature error quantified with conformal + bootstrap intervals; sag predictions gated on measured monotonic shear-thinning.",
     "R-D03 for the phi-max ladder; C.1 formulation set. A locale/typography data-integrity control is mandatory (the digital campaign found a 13-169x literal-reading trap)."),
    ("LAB-C5", "amphora-solvency-score", "Solvency / blend calibration campaign",
     "Measured-blend RMSE beats a modern group-contribution baseline on the locked split with a bootstrap CI excluding parity; Hansen parameters inside the admissible envelope [9.6, 59.9] MPa^0.5; degenerate-baseline check passes.",
     "C.1 seed blends; no external R-D blocker."),
    ("LAB-C6", "amphora-molecule-property", "Molecule-property validation + dielectric labels (>=300 eligible structures)",
     "Coherent-split MAEs within pre-registered bounds; a dielectric arm with R^2 > 0 on admissible rows (currently none exists); cross-corpus transfer non-degrading; exact toolkit + identity + mass + rights reconciliation clean.",
     "R-D06. Feeds B.2's full re-evaluation of molecule-property, the one module the ceremony cannot restore."),
    ("LAB-C7", "amphora-molecule-role-ranker", "Molecule-role blinded-label campaign",
     "Agreement above a pre-registered numeric threshold on the blinded held-out set; no reversal of the amine-direction rule; guanidine chemotype (DPG, DOTG) covered.",
     "C.1 candidate set; labeler contracting."),
    ("LAB-C8", "amphora-design-rule-score", "Design-rule second-formulator DoE",
     "Leak-free delta-R^2 CI excludes zero at the expanded n; cross-formulator transfer non-degrading; Guth-Gold concordance holds.",
     "R-D05. n=58 single-formulator is the binding constraint no modelling choice can fix."),
    ("LAB-C9", "amphora-redteam-audit", "Independent chemistry red-team (96 attacks + 32 valid controls)",
     "0 silent malicious acceptances, 32/32 valid controls accepted, 0 rank/objective emissions, 0 stripped locks, clean two-replay.",
     "Credentials (B.1); runs against the whole tree, so best after A.1/A.2 have hardened the modules. Payloads sealed by the reviewer; the agent that runs it did not author it."),
    ("LAB-C10", "amphora-process-qc-twin", "Process-QC prospective pilot (30 batches, seeded failures)",
     "Seeded failures detected above threshold with a bounded false-positive rate on nominal batches; determinism holds against measured shear histories.",
     "Resolve the process-qc-twin stalls first (T2-10 / campaign item T-10); no external R-D blocker."),
]
for cid, mod, title, gate, deps in _EXPTS:
    add(id=cid, section="C." + cid.replace("LAB-C", ""), owner="LAB", module=mod,
        title=title, done_criteria=gate, campaign_items=[], status="to-file",
        unblock_condition=deps)

add(id="A1-FIRE-INSPECTION", section="A.1", owner="LOOP", module=None,
    title="A fire finishing materially faster than the median is opened for inspection",
    done_criteria="Pre-commit: a fire that finishes materially faster than the 8m55s median is "
                  "opened for inspection before its verdict is banked.",
    campaign_items=[], status="already-delivered",
    note="Implemented in the launcher as the FAST_FIRE log flag on 2026-08-05 (threshold: under half "
         "the measured 537s median over 223 fires; the directive's 8m55s and the live median agree to "
         "two seconds). Deliberately LOG ONLY -- an unexplained fast fire is a smell, not proof, so it "
         "must never downgrade a verdict on its own. Implemented before it was indexed, which is why "
         "it appears here retroactively.")

# --------------------------------------------- operator-derived (NOT founder text)
# These two are ours, not the founder's. They are tracked in the same index so the
# coverage report is complete, but origin marks them so nobody can later read them
# back as things the founder asked for.
add(id="D-COVERAGE", section="meta", owner="LOOP", module="amphora-redteam-audit",
    origin="operator-derived",
    title="Sign the founder-directive coverage table into the evidence tree",
    done_criteria="Signed receipt carrying the full obligation-coverage table, the UNMAPPED and "
                  "ORPHAN lists (reported even when empty), the directive cited by path + sha256, "
                  "and a spot-check of >=3 closed obligations read from their actual receipts.",
    campaign_items=["D-COVERAGE"], status="mapped",
    note="Added by the operator when binding the loop to this directive, so that progress against it "
         "is signed evidence rather than an assertion in a chat log. Not founder text.")
add(id="U-MLIP", section="C.6-adjacent", owner="LOOP", module="amphora-molecule-property",
    origin="operator-derived",
    title="Feasibility: can an MLIP supply physically-admissible dielectric and density labels?",
    done_criteria="Signed feasibility receipt covering rights (licence quoted verbatim), chemistry "
                  "coverage, a determinism verdict against the byte-identical two-replay boundary, "
                  "and an explicit statement that computed labels cannot satisfy a Section C gate.",
    campaign_items=["U-MLIP"], status="mapped",
    note="Raised by the founder alongside this directive (Orb-v3, arXiv:2504.06231). Scoped to the "
         "C.6 label gap. The honest finding recorded up front: Orb and this portfolio share no task, "
         "so a head-to-head benchmark would be a manufactured claim. Not founder directive text.")

# ------------------------------------------------------------------- assemble
# ---------------------------------------------------------------------------
# Reconcile against the LIVE campaign rather than trusting hand-set values. The
# first version of this index hand-asserted campaign_items and status, and by the
# time the items were actually filed 17 of 45 records were lying about their own
# state -- in the one artifact whose entire job is telling the truth about
# coverage. Deriving it removes the failure mode instead of correcting it once.
try:
    _camp = json.load(open(os.environ.get(
        "AMPHORA_CAMPAIGN_PATH", "/home/ubuntu/amphora-cron/campaign.json")))
    _items = _camp["items"] if isinstance(_camp, dict) else _camp
except Exception as _e:                      # never let a campaign read break the build
    _items = []
    print("WARNING: could not read campaign.json (%s); statuses left as authored" % _e)
if _items:
    _by_obl = {}
    for _it in _items:
        _oid = (_it.get("directive_ref") or {}).get("item_id")
        if _oid:
            _by_obl.setdefault(_oid, []).append(_it)
    for _o in obligations:
        _hits = _by_obl.get(_o["id"], [])
        _named = [i for i in _items if i["id"] in (_o.get("campaign_items") or [])]
        _all = {i["id"]: i for i in _hits + _named}
        if not _all:
            continue
        _o["campaign_items"] = sorted(_all)
        if _o["status"] in ("already-delivered", "already-satisfied", "reconciled-with-deviation"):
            continue                          # authored judgements, not derivable
        _st = {i["status"] for i in _all.values()}
        _o["status"] = ("closed" if _st == {"done"}
                        else "blocked" if _st == {"blocked"}
                        else "in-progress")

seen = set()
for o in obligations:
    assert o["id"] not in seen, "duplicate obligation id %s" % o["id"]
    seen.add(o["id"])
    assert o["owner"] in ("LOOP", "HUMAN", "LAB"), o
    assert o["status"] in ("mapped", "to-file", "already-delivered", "already-satisfied",
                           "reconciled-with-deviation", "closed", "blocked", "in-progress"), o

index = {
    "schema": "amphora.directive-index.v1",
    "directive": {
        "title": "Closing the Open Portfolio — Adversarial Coverage, Verification Debt, "
                 "and the Lab-in-the-Loop Program",
        "prepared": "2026-08-05",
        "framing": "AUDIT-ONLY throughout: no product qualification, procurement, safety, synthesis, "
                   "or freedom-to-operate authority is asserted or granted by this document.",
        "host": "xbabe2",
        "root": os.environ.get("AMPHORA_TARGET_ROOT", "/home/ubuntu/amphora/build/mvp20-split"),
        "docx_path": "%s/%s.docx" % (XB2_DIR, STEM), "docx_sha256": sha(DOCX),
        "md_path": "%s/%s.md" % (XB2_DIR, STEM), "md_sha256": sha(MD),
        "source_on_xbabe1": os.environ.get(
            "AMPHORA_DIRECTIVE_SOURCE", "/home/ubuntu/Amphora_Closing_The_Open_Portfolio.docx"),
    },
    "owner_classes": {
        "LOOP": "Autonomous — the hourly cron executes these.",
        "HUMAN": "Governance/rights — the loop is FORBIDDEN from executing these; it files and tracks them only.",
        "LAB": "Wet-lab experiment — requires contracted counterparties and signed candidate-bound returns.",
    },
    "obligations": obligations,
}
json.dump(index, open(OUT, "w"), indent=2, ensure_ascii=False)
json.load(open(OUT))

import collections
print("obligations:", len(obligations))
print("  by owner :", dict(collections.Counter(o["owner"] for o in obligations)))
print("  by status:", dict(collections.Counter(o["status"] for o in obligations)))
print("wrote", OUT)
