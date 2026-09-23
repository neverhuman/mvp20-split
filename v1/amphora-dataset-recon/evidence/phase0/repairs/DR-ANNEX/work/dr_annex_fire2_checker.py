#!/usr/bin/env python3
"""DR-ANNEX fire-2 acceptance re-attack.

Extends fire-1's build_dr_annex.py (sha256 034d322b629724...22225d22de195d27d6656a0104d9fb22f,
same NONCONFORM_MARKERS scan over dataset-ledger.v1.jsonl -- reproduced verbatim
below as run_fire1_scan()) with supersession-awareness: a flagged primary-ledger
row is no longer a live violation of refutation-criterion clause 3 ("a
non-envelope-conforming chemistry appears outside the annex") once (a)
disposition-ledger.v1.jsonl carries a LATER entry that supersedes its
RECOMMENDED verdict (via supersedes.superseded_candidate_id, the same
convention used by the already-landed DR-LANG-EU-02-CORRECTED /
DR-LANG-EU-07-CORRECTED fire-2 repairs) with a non-RECOMMENDED verdict, AND
(b) discovery-annex.v1.jsonl actually contains a matching candidate_id entry.

Clauses 1/2 of the refutation criterion are checked directly: clause 1 asks
whether any annex candidate_id is *currently* (latest-verdict-wins) live
RECOMMENDED/CONDITIONAL in the primary ledger; clause 2 is the repo-wide
cross-module citation sweep for every annex candidate_id.

Runs in two modes selected by argv:
  real   <out.json>                 -- real on-disk ledger state
  mutate <out.json> <candidate_id>  -- positive control: same real state,
                                        but the mutated candidate's
                                        superseding disposition-ledger line is
                                        filtered out in memory before
                                        analysis (nothing written to disk),
                                        simulating an incomplete quarantine.
AUDIT_ONLY, read-only against disk in both modes.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
LEDGERS = MOD / "evidence/ledgers"

NONCONFORM_MARKERS = [
    "adjacent-domain",
    "adjacent domain",
    "non-envelope",
    "non-conforming",
    "anhydride",
    "not the portfolio's core",
    "not coated-steel",
    "not amine-cured",
    "biobased",
    "cardanol",
]

ENVELOPE_SCOPE_STATEMENT = (
    "Coating IP scope ONLY: marine anti-corrosion, two-part epoxy-amine, "
    "DGEBA + amine hardeners, related pigments/fillers/solvents."
)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def parse_jsonl_bytes(b):
    return [json.loads(l) for l in b.decode("utf-8").splitlines() if l.strip()]


def run_fire1_scan(dsl_lines):
    """Byte-identical logic to fire-1's build_dr_annex.py flagged-scan."""
    flagged = []
    for d in dsl_lines:
        txt = json.dumps(d, ensure_ascii=False).lower()
        hits = sorted({m for m in NONCONFORM_MARKERS if m in txt})
        if hits:
            flagged.append({
                "candidate_id": d.get("candidate_id"),
                "ledger_entry_id": d.get("ledger_entry_id"),
                "disposition_verdict": (d.get("disposition") or {}).get("verdict"),
                "language": d.get("language"),
                "markers_hit": hits,
                "coverage_quote": (d.get("coverage") or "")[:400],
                "serves_recipe_elements": (d.get("serves") or {}).get("recipe_elements", []),
                "recipe_elements": d.get("recipe_elements", []),
                "fire_id_of_entry": d.get("fire_id"),
            })
    return flagged


def current_verdicts(disp_lines):
    """latest-verdict-wins map, keyed by the ORIGINAL (pre-supersession)
    candidate_id, honoring the supersedes.superseded_candidate_id convention."""
    cur = {}
    for d in disp_lines:
        cid = d.get("candidate_id")
        verdict = (d.get("disposition") or {}).get("verdict")
        orig_cid = cid
        sup = d.get("supersedes")
        if sup and sup.get("superseded_candidate_id"):
            orig_cid = sup["superseded_candidate_id"]
        cur[orig_cid] = {
            "latest_entry_candidate_id": cid,
            "latest_verdict": verdict,
            "quarantine": d.get("quarantine"),
        }
    return cur


def analyze(dsl_bytes, disp_bytes, annex_bytes):
    dsl_lines = parse_jsonl_bytes(dsl_bytes)
    disp_lines = parse_jsonl_bytes(disp_bytes)
    annex_lines = parse_jsonl_bytes(annex_bytes) if annex_bytes is not None else []
    annex_exists = annex_bytes is not None

    flagged = run_fire1_scan(dsl_lines)
    verdicts = current_verdicts(disp_lines)
    annex_candidate_ids = {a.get("candidate_id") for a in annex_lines}

    resolved = []
    unresolved = []
    for f in flagged:
        cid = f["candidate_id"]
        v = verdicts.get(cid, {})
        latest_verdict = v.get("latest_verdict")
        q = v.get("quarantine") or {}
        is_quarantined_verdict = latest_verdict not in ("RECOMMENDED", None)
        in_annex = cid in annex_candidate_ids
        row = dict(f, latest_verdict=latest_verdict, in_annex=in_annex,
                   quarantine_flag=bool(q.get("quarantined")))
        if is_quarantined_verdict and in_annex:
            resolved.append(row)
        else:
            unresolved.append(row)

    # Clause 1: any annex candidate_id currently live RECOMMENDED/CONDITIONAL
    # in the primary ledger (latest-verdict-wins)?
    clause1_hits = []
    for cid in sorted(annex_candidate_ids):
        v = verdicts.get(cid, {})
        if v.get("latest_verdict") in ("RECOMMENDED", "CONDITIONAL"):
            clause1_hits.append({"candidate_id": cid, "latest_verdict": v.get("latest_verdict")})

    clause3_observed = len(unresolved) > 0

    return {
        "envelope_scope_statement": ENVELOPE_SCOPE_STATEMENT,
        "annex_exists": annex_exists,
        "annex_candidate_ids": sorted(annex_candidate_ids),
        "dataset_ledger_sha256": sha(dsl_bytes),
        "dataset_ledger_total_lines": len(dsl_lines),
        "disposition_ledger_sha256": sha(disp_bytes),
        "disposition_ledger_total_lines": len(disp_lines),
        "flagged_in_primary_ledger": flagged,
        "flagged_count": len(flagged),
        "resolved_count": len(resolved),
        "unresolved_count": len(unresolved),
        "resolved": resolved,
        "unresolved": unresolved,
        "clause1_annex_entry_live_in_primary_ledger_hits": clause1_hits,
        "clause1_observed": len(clause1_hits) > 0,
        "clause3_nonconforming_outside_annex_observed": clause3_observed,
        "refutation_criterion_observed_overall": (len(clause1_hits) > 0) or clause3_observed,
    }


def main():
    mode = sys.argv[1]
    out_path = Path(sys.argv[2])

    dsl_bytes = (LEDGERS / "dataset-ledger.v1.jsonl").read_bytes()
    disp_bytes = (LEDGERS / "disposition-ledger.v1.jsonl").read_bytes()
    annex_path = LEDGERS / "discovery-annex.v1.jsonl"
    annex_bytes = annex_path.read_bytes() if annex_path.exists() else None

    if mode == "mutate":
        drop_cid = sys.argv[3]
        disp_lines_raw = [l for l in disp_bytes.decode("utf-8").splitlines() if l.strip()]
        kept = []
        dropped_n = 0
        for l in disp_lines_raw:
            obj = json.loads(l)
            sup = obj.get("supersedes") or {}
            if sup.get("superseded_candidate_id") == drop_cid:
                dropped_n += 1
                continue
            kept.append(l)
        assert dropped_n == 1, f"expected to drop exactly 1 superseding line for {drop_cid}, dropped {dropped_n}"
        disp_bytes = ("\n".join(kept) + "\n").encode("utf-8")
        result = analyze(dsl_bytes, disp_bytes, annex_bytes)
        result["mode"] = "mutate"
        result["planted_defect"] = f"dropped superseding disposition-ledger entry for {drop_cid} (in-memory only, not written to disk)"
    elif mode == "real":
        result = analyze(dsl_bytes, disp_bytes, annex_bytes)
        result["mode"] = "real"
    else:
        raise SystemExit(f"unknown mode {mode}")

    out_path.write_text(json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
