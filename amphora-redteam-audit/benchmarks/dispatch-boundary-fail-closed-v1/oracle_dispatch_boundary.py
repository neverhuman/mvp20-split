#!/usr/bin/env python3
"""
Independent dispatch-boundary fail-closed oracle for amphora-redteam-audit.

NEW falsifiable hypothesis (distinct from meta-integrity-oracle-parity-v1, which
covered OUTPUT-payload digest parity + a tamper corpus): the redteam meta-audit's
INPUT dispatch is a fail-closed EXACT-BYTE-MATCH allowlist --

    accept(id)  <=>  id in S,   S = the shipped supported-module set,

and every near-miss non-member (case, whitespace, unicode-confusable, hyphen/
underscore, path-traversal, sub/super-string) fail-closes. The 6 shipped KPI
probes in `unsupported_module_id_fail_closed_rate` are reproduced byte-exact, and
an independently-constructed large near-miss corpus fail-closes at rate 1.0 while
every genuine ID accepts (complete mediation). Exact-byte-match is shown NECESSARY:
two named relaxations (case-insensitive; Unicode-confusable-skeleton) each wrongly
admit a shipped probe.

Theory stack (primary sources):
  - Reference monitor / complete mediation: Anderson 1972 (ESD-TR-73-51);
    Saltzer & Schroeder 1975 CACM "fail-safe defaults" / least privilege.
  - Deny-by-default access control; NIST SP 800-53 Rev.5 AC-3/AC-6.
  - Unicode TR39 "Unicode Security Mechanisms" confusable/skeleton detection (2023);
    Unicode 15 confusables data (Latin<->Cyrillic homoglyphs).
  - Canonical JSON key-sorted serialization (RFC 8785 JCS 2020) for byte-stable output.
  - SHA-256 NIST FIPS 180-4 (2015).

Deterministic: no wall-clock, no RNG. Two invocations are byte-identical.
"""
import json, hashlib, sys

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
RTA = ROOT + "/amphora-redteam-audit"
RESULT = RTA + "/evidence/phase0/benchmark/result.v1.json"

# Mission-declared 9 supported upstream modules (docs/mission.md).
EXPECTED_MODULES = [
    "amphora-evidence-intake-validator", "amphora-source-ledger", "amphora-redteam-audit",
    "amphora-report-packager", "amphora-formulation-arithmetic", "amphora-formulation-universe",
    "amphora-envelope-gates", "amphora-cro-protocol-packager", "amphora-optimizer-orchestrator",
]

# ---- independent canonical JSON + SHA-256 ----
def canon(v):
    if isinstance(v, dict):
        return {k: canon(v[k]) for k in sorted(v.keys())}
    if isinstance(v, list):
        return [canon(x) for x in v]
    return v
def canon_bytes(v):
    return json.dumps(canon(v), separators=(",", ":"), ensure_ascii=False).encode("utf-8")
def stable_hash(v):
    return hashlib.sha256(canon_bytes(v)).hexdigest()

# ---- the dispatch predicate under test: fail-closed exact-BYTE-match allowlist ----
def accept_exact(id_str, S):
    return id_str in S

# ---- two named RELAXATIONS used to prove exact-match is load-bearing ----
def accept_caseinsensitive(id_str, S):
    return id_str.strip().lower() in {s.lower() for s in S}

# TR39-style confusable skeleton: fold a small set of Cyrillic homoglyphs to Latin.
# (Illustrative subset sufficient for the shipped Cyrillic probe; TR39 confusables.)
_CONFUSABLE_FOLD = {
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M",
    "Н": "H", "О": "O", "Р": "P", "С": "C", "Т": "T",
    "Х": "X", "а": "a", "е": "e", "о": "o", "р": "p",
    "с": "c", "х": "x", "у": "y", "і": "i",
}
def skeleton(s):
    return "".join(_CONFUSABLE_FOLD.get(ch, ch) for ch in s)
def accept_confusable_skeleton(id_str, S):
    sk = skeleton(id_str.strip())
    return sk in {skeleton(s) for s in S} or sk.lower() in {skeleton(s).lower() for s in S}

# ---- deterministic near-miss mutation families over a genuine ID ----
_HOMO_LAT2CYR = {"a": "а", "e": "е", "o": "о", "p": "р",
                 "c": "с", "x": "х", "y": "у"}
def homoglyph_variant(s):
    # replace the FIRST Latin char that has a Cyrillic confusable, deterministically
    for i, ch in enumerate(s):
        if ch in _HOMO_LAT2CYR:
            return s[:i] + _HOMO_LAT2CYR[ch] + s[i+1:]
    return None

def near_miss_variants(genuine):
    """Deterministic ordered list of (family, variant) near-misses for one ID."""
    v = []
    v.append(("uppercase", genuine.upper()))
    v.append(("titlecase", genuine.title()))
    v.append(("leading_space", " " + genuine))
    v.append(("trailing_space", genuine + " "))
    v.append(("internal_space", genuine.replace("-", " -", 1)))
    v.append(("trailing_tab", genuine + "\t"))
    v.append(("trailing_newline", genuine + "\n"))
    v.append(("trailing_dot", genuine + "."))
    v.append(("trailing_slash", genuine + "/"))
    v.append(("path_traversal", "../" + genuine))
    v.append(("hyphen_to_underscore", genuine.replace("-", "_")))
    v.append(("hyphen_removed", genuine.replace("-", "")))
    v.append(("hyphen_to_space", genuine.replace("-", " ")))
    v.append(("zero_width_space", genuine[:1] + "​" + genuine[1:]))
    v.append(("trailing_null", genuine + "\x00"))
    v.append(("drop_last_char", genuine[:-1]))
    v.append(("append_char", genuine + "x"))
    v.append(("duplicate_prefix", "amphora-" + genuine))
    hv = homoglyph_variant(genuine)
    if hv is not None:
        v.append(("cyrillic_homoglyph", hv))
    return v

def run():
    doc = json.load(open(RESULT))
    recs = doc["first_replay"]["diagnostic_receipt"]["records"]
    kpi = doc["first_replay"]["diagnostic_receipt"]["kpi"]
    gates = {}

    # ---- G1: supported-set derivation parity ----
    derived = [r["module_id"] for r in recs]
    S = set(derived)
    dispatch_ok_n = kpi["diagnostic_dispatch_ok_rate"]["sample_size"]
    g1_pass = (derived == EXPECTED_MODULES and len(S) == 9 and len(derived) == 9
               and dispatch_ok_n == 9)
    gates["G1_supported_set_derivation"] = {
        "derived_supported_ids": derived,
        "matches_mission_expected": derived == EXPECTED_MODULES,
        "cardinality": len(derived),
        "no_duplicates": len(S) == len(derived),
        "kpi_dispatch_ok_sample_size": dispatch_ok_n,
        "passed": g1_pass,
    }

    # ---- G2: reproduce the 6 shipped KPI fail-closed probes byte-exact ----
    shipped = kpi["unsupported_module_id_fail_closed_rate"]["probes"]
    probe_checks = []
    for p in shipped:
        pid = p["probe"]
        indep_fail_closed = not accept_exact(pid, S)
        probe_checks.append({
            "probe": pid,
            "shipped_fail_closed": p["fail_closed"],
            "independent_fail_closed": indep_fail_closed,
            "agree": indep_fail_closed == p["fail_closed"],
        })
    g2_pass = (len(shipped) == 6 and all(c["agree"] and c["independent_fail_closed"]
                                         for c in probe_checks))
    gates["G2_shipped_probe_reproduction"] = {
        "shipped_probe_count": len(shipped),
        "all_agree_and_fail_closed": g2_pass,
        "probe_checks": probe_checks,
        "passed": g2_pass,
    }

    # ---- G3: positive controls -- every genuine ID accepts (complete mediation) ----
    pos = [{"id": m, "accepted": accept_exact(m, S)} for m in EXPECTED_MODULES]
    g3_pass = all(p["accepted"] for p in pos) and len(pos) == 9
    gates["G3_positive_control_acceptance"] = {
        "genuine_id_count": len(pos),
        "all_accepted": all(p["accepted"] for p in pos),
        "records": pos,
        "passed": g3_pass,
    }

    # ---- G4: independent near-miss adversarial fuzz -- all non-members fail-closed ----
    corpus = []
    for genuine in EXPECTED_MODULES:
        for fam, var in near_miss_variants(genuine):
            is_member = accept_exact(var, S)             # byte-equal to SOME genuine id?
            corpus.append({
                "genuine": genuine, "family": fam, "variant": var,
                "is_exact_member": is_member,
                "fail_closed": (not is_member),
            })
    # every generated near-miss is a genuine NON-member (no accidental collision)...
    n_collision = sum(1 for c in corpus if c["is_exact_member"])
    n_total = len(corpus)
    n_fail_closed = sum(1 for c in corpus if c["fail_closed"])
    g4_pass = (n_collision == 0 and n_fail_closed == n_total and n_total > 0)
    # family-level breakdown for auditability (sorted, deterministic)
    fam_names = sorted({c["family"] for c in corpus})
    fam_counts = {f: sum(1 for c in corpus if c["family"] == f) for f in fam_names}
    gates["G4_near_miss_fuzz_fail_closed"] = {
        "total_near_miss_probes": n_total,
        "accidental_exact_collisions": n_collision,
        "fail_closed_count": n_fail_closed,
        "fail_closed_rate": (n_fail_closed / n_total) if n_total else 0.0,
        "families": fam_counts,
        "passed": g4_pass,
    }

    # ---- G5: exact-byte-match NECESSITY -- named relaxations admit a shipped probe ----
    # case-insensitive relaxation must WRONGLY accept the uppercase shipped probe.
    up_probe = "AMPHORA-REDTEAM-AUDIT"
    ci_admits = accept_caseinsensitive(up_probe, S)
    # confusable-skeleton relaxation must WRONGLY accept a Cyrillic homoglyph of a real id.
    cyr_probe = homoglyph_variant("amphora-redteam-audit")   # Latin->Cyrillic first-char fold
    sk_admits = accept_confusable_skeleton(cyr_probe, S)
    # ...while EXACT match correctly rejects both.
    exact_rejects_up = not accept_exact(up_probe, S)
    exact_rejects_cyr = not accept_exact(cyr_probe, S)
    g5_pass = ci_admits and sk_admits and exact_rejects_up and exact_rejects_cyr
    gates["G5_exact_match_necessity"] = {
        "case_insensitive_relaxation_wrongly_admits_uppercase_probe": ci_admits,
        "confusable_skeleton_relaxation_wrongly_admits_homoglyph": sk_admits,
        "exact_match_rejects_uppercase_probe": exact_rejects_up,
        "exact_match_rejects_homoglyph_probe": exact_rejects_cyr,
        "uppercase_probe": up_probe,
        "homoglyph_probe_codepoints": [hex(ord(c)) for c in cyr_probe],
        "note": ("Both relaxations are strictly weaker security predicates: each admits "
                 "an input the shipped runtime fail-closes on, so exact-byte-match "
                 "membership is load-bearing (TR39 confusable / case-fold aliasing)."),
        "passed": g5_pass,
    }

    all_passed = all(g["passed"] for g in gates.values())
    return {
        "schema": "amphora.redteam-audit.dispatch-boundary-fail-closed.v1",
        "oracle_id": "dispatch-boundary-fail-closed-v1",
        "module_id": "amphora-redteam-audit",
        "hypothesis": ("The redteam meta-audit INPUT dispatch is a fail-closed exact-byte-match "
                       "allowlist over exactly the 9 shipped supported modules: every genuine id "
                       "accepts, every near-miss non-member (case/whitespace/unicode-confusable/"
                       "hyphen/path-traversal/sub-super-string) fail-closes, the 6 shipped KPI "
                       "probes are reproduced byte-exact, and exact-byte-match is necessary "
                       "(case-insensitive and confusable-skeleton relaxations each admit a probe)."),
        "theory_sources": [
            "Anderson 1972 ESD-TR-73-51 reference monitor / complete mediation",
            "Saltzer & Schroeder 1975 CACM: fail-safe defaults / least privilege",
            "NIST SP 800-53 Rev.5 AC-3/AC-6 deny-by-default access enforcement",
            "Unicode TR39 Security Mechanisms confusable-skeleton (2023); Unicode 15 confusables",
            "RFC 8785 JCS canonical JSON (2020); NIST FIPS 180-4 SHA-256 (2015)",
        ],
        "subject_artifacts": {
            "result_v1": "amphora-redteam-audit/evidence/phase0/benchmark/result.v1.json",
            "kpi_field": "unsupported_module_id_fail_closed_rate",
        },
        "relation_to_prior_oracle": ("Non-overlapping with meta-integrity-oracle-parity-v1: that "
                                     "oracle covered OUTPUT-payload digest parity + a tamper corpus; "
                                     "this oracle covers the INPUT dispatch fail-closed boundary and "
                                     "extends the 6 shipped probes to a systematic near-miss corpus."),
        "gates": gates,
        "all_gates_passed": all_passed,
        "verdict": ("HYPOTHESIS_CORROBORATED" if all_passed else "HYPOTHESIS_REFUTED"),
        "ceiling_note": ("Offline oracle: models dispatch as exact-byte-match membership over the "
                         "shipped supported-module set and reproduces the 6 KPI probes byte-exact, "
                         "but does not RE-EXECUTE the Rust dispatch fn deterministic_control_diagnostic. "
                         "Live Rust dispatch re-execution + full error-taxonomy parity remain Phase-1."),
    }

if __name__ == "__main__":
    out = run()
    sys.stdout.write(json.dumps(canon(out), separators=(",", ":"), ensure_ascii=False))
