#!/usr/bin/env python3
"""load-bearing-classification-completeness-v1

Attacks the completeness claim underlying every external-verification KPI this
module has signed to date (hardener-tds-external-verification-v1, W-ING2,
pigment-density-second-source-verification-v1, constant-crosscheck-v1
Check-1/Check-2): that facts.json's own `load_bearing` boolean correctly
identifies every constant that needs independent second-source verification.
All four of those receipts filter their scope on `load_bearing == true` (or,
for pigment-density-second-source-verification-v1, explicitly claim barytes+
talc are "the LAST two load-bearing pigment density constants ... needing
... corroboration"). This oracle tests that filter against ground truth:
actual numeric consumption by other modules' own signed/live artifacts,
found by grepping the whole mvp20-split tree (never trusting facts.json's
self-declared flag).

Method:
  1. Load amphora-ingredient-library/reference/mvp20/data/facts.json; take
     every key with load_bearing != true (or absent).
  2. For each such key, grep the ENTIRE portfolio tree (*.py, *.rs) for a
     literal double-quoted reference to the key, excluding (a) this module's
     own tree (evidence/audit-about-the-fact is not downstream consumption)
     and (b) reference/mvp20/data/ mirrors of facts.json itself (a data copy
     is not code consuming the fact).
  3. For every surviving hit, read the matched line; keep it only if the line
     assigns the fact's value to a Python variable (contains `fact(` / `fv(`
     / `facts[` / `facts_doc` a pattern already used throughout this
     portfolio's own audit scripts) -- i.e. genuine numeric consumption, not
     an incidental string match.
  4. For every fact with >=1 surviving hit, check whether the consuming file
     lives under a `/done/` repair directory or a `benchmarks/.../replay_receipt`
     path (i.e. is itself a live signed artifact, not a discarded attempt),
     and independently verify that receipt is DSSE-shaped (payload+signatures)
     -- proof the fact reached a SIGNED downstream KPI, not just a draft.
  5. Cross-check: does the SAME key appear inside a GATED (not
     "report only") admissibility check in any of this module's own audit
     receipts? Search constant-crosscheck-v1 and
     pigment-density-second-source-verification-v1 diagnostics.
  6. Refutation criterion (pre-registered before running step 2-6): the
     completeness claim is REFUTED if >=1 fact exists with load_bearing=false
     in facts.json AND >=1 genuine numeric consumption in a DSSE-signed
     downstream artifact AND zero gated (non-"report only") independent
     second-source check anywhere in this module's own audit trail.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MODULE = ROOT / "amphora-ingredient-library"
FACTS = MODULE / "reference/mvp20/data/facts.json"
LEDGER = ROOT / "logs/falsification-ledger.jsonl"


def sha(b):
    return hashlib.sha256(b).hexdigest()


facts_bytes = FACTS.read_bytes()
facts_sha256 = sha(facts_bytes)
facts_doc = json.loads(facts_bytes)
entries = facts_doc["entries"]

nonlb_keys = sorted(k for k, v in entries.items() if not v.get("load_bearing"))
lb_keys = sorted(k for k, v in entries.items() if v.get("load_bearing"))

CONSUME_MARKERS = ("fact(", "fv(", "facts[", "facts.get(")

# ---- map of "script that consumes a fact" -> "the signed receipt that
# script's own module already produced from that consumption" (established
# by manual inspection this fire: cf_arith_engine.py backs the CF-ARITH done
# receipt, w_t_arith_epa24_audit.py backs the W-T-ARITH done receipt,
# formulation_dimensioned_audit.py backs the redteam-audit benchmark's
# replay receipt). This is ground truth about signed-artifact provenance,
# independent of facts.json's own load_bearing flag. -----------------------
DONE_RECEIPT_MAP = {
    "amphora-formulation-arithmetic/evidence/phase0/repairs/CF-ARITH/work/cf_arith_engine.py":
        "amphora-formulation-arithmetic/evidence/phase0/repairs/CF-ARITH/done/CF-ARITH.done-receipt.v1.dsse.json",
    "amphora-formulation-arithmetic/evidence/phase0/repairs/W-T-ARITH/work/w_t_arith_epa24_audit.py":
        "amphora-formulation-arithmetic/evidence/phase0/repairs/W-T-ARITH/done/W-T-ARITH.done-receipt.v1.dsse.json",
    "amphora-redteam-audit/benchmarks/formulation-arithmetic-dimensioned-v1/formulation_dimensioned_audit.py":
        "amphora-redteam-audit/benchmarks/formulation-arithmetic-dimensioned-v1/replay_receipt.v1.dsse.json",
}


def is_dsse(path: Path):
    try:
        d = json.loads(path.read_text())
    except Exception:
        return False
    if isinstance(d, dict) and "payloadType" in d and "signatures" in d:
        return True
    if isinstance(d, dict) and isinstance(d.get("signature"), dict) and "payloadType" in d["signature"]:
        return True
    return False


per_key = []
for key in nonlb_keys:
    grep = subprocess.run(
        ["grep", "-rn", f'"{key}"', str(ROOT), "--include=*.py", "--include=*.rs"],
        capture_output=True, text=True,
    ).stdout.strip()
    raw_hits = [l for l in grep.split("\n") if l]
    genuine = []
    for line in raw_hits:
        # format: <path>:<lineno>:<content>
        path, lineno, content = line.split(":", 2)
        if "/amphora-ingredient-library/" in path:
            continue
        if "/reference/mvp20/data/" in path:
            continue
        if not any(m in content for m in CONSUME_MARKERS):
            continue
        genuine.append({"file": path.replace(str(ROOT) + "/", ""), "line": int(lineno),
                         "content": content.strip(),
                         "file_sha256": sha(Path(path).read_bytes())})
    if not genuine:
        continue
    consuming_files = sorted({g["file"] for g in genuine})
    signed_consumers = sorted({f for f in consuming_files if f in DONE_RECEIPT_MAP
                                and (ROOT / DONE_RECEIPT_MAP[f]).exists()
                                and is_dsse(ROOT / DONE_RECEIPT_MAP[f])})
    per_key.append({
        "fact_key": key,
        "catalog_value": entries[key].get("value"),
        "catalog_unit": entries[key].get("unit"),
        "load_bearing_flag_in_facts_json": bool(entries[key].get("load_bearing", False)),
        "genuine_numeric_consumption_hits": genuine,
        "consuming_files": consuming_files,
        "signed_downstream_consumers": [DONE_RECEIPT_MAP[f] for f in signed_consumers],
        "reached_signed_downstream_artifact": bool(signed_consumers),
    })

flagged = [r for r in per_key if r["reached_signed_downstream_artifact"]]

downstream_receipt_verification = []
for src, receipt_rel in sorted(set(DONE_RECEIPT_MAP.items())):
    rp = ROOT / receipt_rel
    exists = rp.exists()
    dsse_ok = is_dsse(rp) if exists else False
    downstream_receipt_verification.append({
        "consumer_source_file": src,
        "receipt_path": receipt_rel,
        "receipt_exists": exists,
        "receipt_is_dsse_shaped": dsse_ok,
        "receipt_sha256": sha(rp.read_bytes()) if exists else None,
    })

# cross-check verdicts in the falsification ledger for these receipts
ledger_lines = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
ledger_cross_check = []
for row in downstream_receipt_verification:
    matches = [l for l in ledger_lines if row["receipt_path"] in l.get("receipt", "")]
    ledger_cross_check.append({
        "receipt_path": row["receipt_path"],
        "ledger_entries_found": len(matches),
        "verdicts": [m.get("verdict") for m in matches],
        "modules": sorted({m.get("module") for m in matches}),
    })

# ---- step 5: was the same key ever GATED (not "report only") in this
# module's own audit trail? ---------------------------------------------
crosscheck_src = (MODULE / "evidence/audit/constant-crosscheck-v1/run_crosscheck.py").read_text()
pigment_second_src = (MODULE / "evidence/audit/pigment-density-second-source-verification-v1"
                       / "run_pigment_density_verify.py").read_text()

gated_status = {}
for r in flagged:
    key = r["fact_key"]
    in_pig_ref_diagnostic = f'"{key}"' in crosscheck_src
    in_dens_ref_gate = False  # DENS_REF only covers solvent/resin keys, checked below
    # DENS_REF dict entries are keyed by exact string; PIG_REF is the report-only block.
    # A key is only "gated" if it appears in DENS_REF (Check-2, real pass/fail gate) --
    # not merely PIG_REF (explicitly "Reported only, NOT gated" per the diagnostic's own text).
    dens_ref_block = crosscheck_src.split("PIG_REF = {")[0]
    in_dens_ref_gate = f'"{key}"' in dens_ref_block
    covered_by_pigment_second_source_v1 = f'"{key}"' in pigment_second_src or key in pigment_second_src
    gated_status[key] = {
        "appears_in_constant_crosscheck_v1_PIG_REF_report_only_diagnostic": in_pig_ref_diagnostic,
        "appears_in_constant_crosscheck_v1_DENS_REF_gated_check": in_dens_ref_gate,
        "covered_by_pigment_density_second_source_verification_v1_scope": covered_by_pigment_second_source_v1,
        "any_gated_independent_second_source_check_anywhere_in_module": bool(in_dens_ref_gate or covered_by_pigment_second_source_v1),
    }

refuted_facts = [r["fact_key"] for r in flagged
                 if not gated_status[r["fact_key"]]["any_gated_independent_second_source_check_anywhere_in_module"]]

headline = {
    "n_nonload_bearing_keys_in_facts_json": len(nonlb_keys),
    "n_load_bearing_keys_in_facts_json": len(lb_keys),
    "n_nonload_bearing_keys_with_genuine_downstream_code_consumption": len(per_key),
    "n_nonload_bearing_keys_reaching_a_signed_downstream_artifact": len(flagged),
    "n_of_those_with_zero_gated_second_source_check_anywhere_in_module": len(refuted_facts),
    "refuted_fact_keys": refuted_facts,
}

refutation_criterion = (
    "PRE-REGISTERED: the completeness claim underlying "
    "hardener-tds-verified-constants-kpi.v1 (as extended by W-ING2) and "
    "pigment-density-second-source-verification-v1's own text (\"the LAST two "
    "load-bearing pigment density constants ... needing ... corroboration\") "
    "is REFUTED if >=1 facts.json key marked load_bearing=false is (a) "
    "genuinely consumed as a numeric input by code inside a DSSE-signed "
    "downstream artifact elsewhere in the portfolio, AND (b) never subject to "
    "any GATED (non-\"report only\") independent second-source check anywhere "
    "in this module's own audit trail. Observation: %d such facts found (%s)."
    % (len(refuted_facts), ", ".join(refuted_facts))
)

diag = {
    "schema": "amphora.ingredient-library.load-bearing-classification-completeness.v1",
    "module": "amphora-ingredient-library",
    "run_type": "AUDIT_ONLY",
    "authority": "AUDIT_ONLY",
    "purpose": "Test whether facts.json's self-declared `load_bearing` boolean -- the sole "
               "gating predicate every prior external-verification KPI in this module has used "
               "to scope 'every load-bearing constant externally verified' -- actually matches "
               "real portfolio-wide downstream numeric consumption.",
    "inputs": {"facts_json": "amphora-ingredient-library/reference/mvp20/data/facts.json",
               "facts_json_sha256": facts_sha256,
               "search_root": "mvp20-split (whole tree, *.py and *.rs)"},
    "refutation_criterion": refutation_criterion,
    "per_key_analysis": per_key,
    "flagged_facts_reaching_signed_downstream_artifact": flagged,
    "downstream_receipt_verification": downstream_receipt_verification,
    "ledger_cross_check": ledger_cross_check,
    "gated_status_of_flagged_facts": gated_status,
    "headline": headline,
    "verdict": "CLAIM_REFUTED" if refuted_facts else "CLAIM_SURVIVED",
}

out_dir = MODULE / "evidence/audit/load-bearing-classification-completeness-v1"
out_dir.mkdir(parents=True, exist_ok=True)
canon = json.dumps(diag, indent=2, sort_keys=True).encode()
(out_dir / "diagnostic.canonical.json").write_bytes(canon)
print("headline:", json.dumps(headline, indent=2))
print("verdict:", diag["verdict"])
print("sha256:", sha(canon))
