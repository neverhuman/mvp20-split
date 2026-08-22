#!/usr/bin/env python3
"""
amphora-barrier-corrosion-score / corr-rate-source-lofo-v1
FALSIFICATION ATTACK on evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1
(GroupKFold(group=metallurgical_family, 5-fold) HistGBM R2=0.132087 on the
NIST CORR-DATA classified subset, n=7282, 17 families), "the module's
strongest rights-clean empirical claim", and by extension on the narrow
CLAIM_SURVIVED verdict of corr-rate-family-lofo-v1 (family-weighted mean
LOFO R2=0.015964) and CLAIM_REFUTED verdict of corr-rate-marine-envelope-v1
(environment-axis shift, R2=-0.450740).

WHY THIS IS THE NEXT ESCALATION, NOT A REPEAT:
Every prior attack on this KPI has varied either the CV GROUPING AXIS
(material string -> metallurgical family -> true leave-one-family-out) or
the ENVIRONMENT axis (marine vs non-marine deployment domain). None has
varied the DATA-PROVENANCE axis: NIST CORR-DATA is itself a compilation of
measurements from 220 distinct original literature sources (source_text
field: corrosion handbooks, alloy-vendor bulletins, individual journal
papers, spanning multiple decades, testing methodologies, and laboratories
-- e.g. "A Guide to Corrosion Resistance, Climax Molybdenum Company, 1981"
vs "Haynes International, 1984" vs "Metals Handbook, Ninth Edition, ASM
International, 1987"). A model that generalizes only WITHIN a source's own
testing methodology/reporting convention (rounding, exposure duration,
specimen prep, author-specific rating-to-rate conversion) but not ACROSS
independent sources would still show a strong family-safe or even
per-family LOFO R2, because most sources are family-specialized (e.g.
Climax Molybdenum reports mostly molybdenum/nickel alloys; Haynes reports
mostly cobalt/nickel superalloys) -- family-safe splits do not control for
this. This is a genuine source-safe / group-safe split in the sense of the
assignment brief.

ATTACK: true Leave-One-Source-Out (LOSO) on the IDENTICAL classified
subset (n=7282, 17 families) used by corr-rate-family-safe-v1 and
corr-rate-family-lofo-v1, with the SAME feature engineering, HistGBM
hyperparameters, and seed=0, copied byte-for-byte (verbatim: comp_vector,
env_features, load, build_matrix, metrics, classify_family, COMPOSITION,
_FAMILY_RULES). The ONLY new variable is the CV split: GroupKFold with
groups=source_text (n_splits = n_distinct_sources_in_classified_subset),
instead of groups=metallurgical_family.

PRE-REGISTERED REFUTATION CRITERION (declared before running/inspecting
results): The promoted KPI implicitly asserts the model learns a
transferable structure-composition-environment -> corrosion-rate
relationship, not merely a source-specific reporting convention. This is
REFUTED if EITHER:
  (a) the source-count-weighted (unweighted-per-source) mean LOSO R2,
      averaged over all sources with n_test>=20 rows in the classified
      subset, is <= 0.0; OR
  (b) a majority (>50%) of those n>=20 eligible sources individually
      score LOSO R2 <= 0.0.
It SURVIVES if the source-weighted mean LOSO R2 > 0 AND a majority of
eligible sources individually score R2 > 0, even if both are reduced
relative to the family-safe/LOFO numbers (LOSO is a different and
potentially harder axis; some reduction is expected and is not itself a
refutation).

Determinism: OMP_NUM_THREADS=1, fixed seed, GroupKFold(n_splits=n_sources)
with groups=source_text label (one source per fold when n_splits==n_groups,
verified by assertion), rounded canonical output -> byte-stable two-replay
SHA-256 gate.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
import json, hashlib, math, sys, re
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
import sklearn

SRC = "feedback/v1/derived/nist_corr_reference.json"
SEED = 0
NDEC = 6
MIN_ELIGIBLE_N = 20

# ---------------------------------------------------------------------------
# VERBATIM from corr-rate-family-safe-v1/corr_rate_family_safe.py and
# corr-rate-family-lofo-v1/corr_rate_family_lofo.py, EXCEPT load() also
# carries source_text through (new field, does not change any row's
# inclusion/exclusion logic or feature values).
ELEMENTS = ["fe", "cr", "ni", "mo", "cu", "ti", "zr", "nb", "ta", "co",
            "w", "al", "mn", "si", "c", "pb", "sn", "ag", "pt", "au"]

COMPOSITION = {
    "316l": {"fe": 67, "cr": 17, "ni": 12, "mo": 2.5, "mn": 1.5},
    "316":  {"fe": 67, "cr": 17, "ni": 12, "mo": 2.5, "mn": 1.5},
    "317":  {"fe": 63, "cr": 19, "ni": 13, "mo": 3.5, "mn": 1.5},
    "304l": {"fe": 70, "cr": 18, "ni": 9, "mn": 1.5},
    "304":  {"fe": 70, "cr": 18, "ni": 9, "mn": 1.5},
    "321":  {"fe": 70, "cr": 18, "ni": 10, "ti": 0.4, "mn": 1.5},
    "347":  {"fe": 69, "cr": 18, "ni": 11, "nb": 0.8, "mn": 1.5},
    "410":  {"fe": 86, "cr": 12.5, "mn": 1},
    "430":  {"fe": 82, "cr": 17, "mn": 1},
    "2205": {"fe": 68, "cr": 22, "ni": 5, "mo": 3, "mn": 1.5},
    "carpenter 20": {"fe": 35, "cr": 20, "ni": 34, "mo": 2.5, "cu": 3.3, "nb": 0.5},
    "alloy 20":     {"fe": 35, "cr": 20, "ni": 34, "mo": 2.5, "cu": 3.3, "nb": 0.5},
    "20cb":         {"fe": 35, "cr": 20, "ni": 34, "mo": 2.5, "cu": 3.3, "nb": 0.5},
    "hastelloy c-276": {"ni": 57, "cr": 16, "mo": 16, "w": 3.5, "fe": 5, "co": 2.5},
    "hastelloy c-22":  {"ni": 56, "cr": 22, "mo": 13, "w": 3, "fe": 3, "co": 2.5},
    "alloy c-276": {"ni": 57, "cr": 16, "mo": 16, "w": 3.5, "fe": 5, "co": 2.5},
    "alloy c-22":  {"ni": 56, "cr": 22, "mo": 13, "w": 3, "fe": 3, "co": 2.5},
    "hastelloy c": {"ni": 57, "cr": 16, "mo": 16, "w": 3.5, "fe": 5, "co": 2.5},
    "hastelloy b": {"ni": 66, "mo": 28, "fe": 5, "co": 1},
    "inconel 625": {"ni": 61, "cr": 22, "mo": 9, "nb": 3.5, "fe": 3},
    "alloy 625":   {"ni": 61, "cr": 22, "mo": 9, "nb": 3.5, "fe": 3},
    "inconel 600": {"ni": 76, "cr": 15.5, "fe": 8},
    "alloy 600":   {"ni": 76, "cr": 15.5, "fe": 8},
    "incoloy 825": {"ni": 42, "fe": 30, "cr": 21.5, "mo": 3, "cu": 2.2, "ti": 0.9},
    "alloy 825":   {"ni": 42, "fe": 30, "cr": 21.5, "mo": 3, "cu": 2.2, "ti": 0.9},
    "incoloy 800": {"ni": 32, "fe": 46, "cr": 21},
    "alloy 800":   {"ni": 32, "fe": 46, "cr": 21},
    "monel 400":   {"ni": 66, "cu": 32, "fe": 2},
    "alloy 400":   {"ni": 66, "cu": 32, "fe": 2},
    "monel":       {"ni": 66, "cu": 32, "fe": 2},
    "nickel 200":  {"ni": 99.5},
    "nickel 201":  {"ni": 99.5},
    "70-30 cupronickel": {"cu": 69, "ni": 30, "fe": 0.6},
    "90-10 cupronickel": {"cu": 88, "ni": 10, "fe": 1.4},
    "cupronickel": {"cu": 79, "ni": 20},
    "aluminum bronze": {"cu": 88, "al": 9, "fe": 3},
    "ampco":       {"cu": 88, "al": 9, "fe": 3},
    "admiralty":   {"cu": 71, "zn": 28, "sn": 1},
    "titanium, grade 7": {"ti": 99.8, "pd": 0.15},
    "titanium":    {"ti": 99.8},
    "zr702":       {"zr": 99.2},
    "zr705":       {"zr": 95, "nb": 2.5},
    "zirconium":   {"zr": 99.2},
    "tantalum":    {"ta": 100},
    "niobium":     {"nb": 100},
    "columbium":   {"nb": 100},
    "platinum":    {"pt": 100},
    "silver":      {"ag": 100},
    "gold":        {"au": 100},
    "chemical lead": {"pb": 99.9},
    "lead":        {"pb": 99.9},
    "tin":         {"sn": 99},
    "carbon steel": {"fe": 99, "mn": 0.6, "c": 0.2},
    "cast iron":   {"fe": 93, "c": 3.5, "si": 2.2},
    "mild steel":  {"fe": 99, "mn": 0.6, "c": 0.15},
    "aluminum":    {"al": 99},
    "copper":      {"cu": 99.9},
    "nickel":      {"ni": 99},
}
_COMP_KEYS = sorted(COMPOSITION.keys(), key=len, reverse=True)


def comp_vector(material):
    m = material.lower()
    for k in _COMP_KEYS:
        if k in m:
            d = COMPOSITION[k]
            return [float(d.get(e, 0.0)) for e in ELEMENTS], True
    return [float("nan")] * len(ELEMENTS), False


def env_features(env):
    e = env.lower()
    def has(*ws): return float(any(w in e for w in ws))
    chloride = has("chlor", "hcl", "seawater", "sea water", "brine", "muriatic")
    fluoride = has("fluor", "hf ")
    bromide = has("brom")
    halide = float(bool(chloride or fluoride or bromide or has("iodide", "iodine")))
    ox_acid = has("nitric", "chromic", "ferric chlor", "hypochlor", "perchlor",
                  "nitrate", "peroxide", "permanganat")
    red_acid = has("hydrochloric", "hydrofluoric", "phosphoric", "formic",
                   "acetic", "sulfurous", "sulphurous", "hydrobromic", "oxalic",
                   "tartaric", "citric", "lactic")
    org_acid = has("acetic", "formic", "oxalic", "tartaric", "citric", "lactic",
                   "propionic", "butyric", "maleic")
    sulfuric = has("sulfuric", "sulphuric")
    alkali = has("hydroxide", "ammoni", "amine", "carbonate", "caustic", "koh",
                 "naoh", "lime")
    marine = has("seawater", "sea water", "marine", "atmospheric")
    salt = has("chloride", "sulfate", "sulphate", "nitrate", "bromide",
               "carbonate", "phosphate", "acetate") and not (ox_acid or red_acid)
    water = float(e.strip() in ("water", "distilled water", "fresh water",
                                "deionized water"))
    is_acid = float(bool(ox_acid or red_acid or sulfuric or "acid" in e))
    return [chloride, fluoride, bromide, halide, ox_acid, red_acid, org_acid,
            sulfuric, alkali, marine, salt, water, is_acid]


def load():
    raw = open(SRC, "rb").read()
    src_sha = hashlib.sha256(raw).hexdigest()
    data = json.loads(raw)
    rows = []
    for x in data:
        v = x.get("metric_value")
        mf = x.get("metric_family") or ""
        if v is None or "rate" not in mf:
            continue
        rate = float(v)
        if mf == "rate_mils_per_year":
            rate = rate * 0.0254
        if rate <= 0:
            continue
        mat = str(x.get("material") or "").strip()
        env = str(x.get("environment") or "").strip()
        if not mat or not env:
            continue
        temp = x.get("temperature_c")
        source = str(x.get("source_text") or "").strip()
        rows.append((mat, env, temp, math.log10(rate), source))
    rows.sort(key=lambda r: (r[0], r[1], (r[2] if r[2] is not None else -999.0), r[3], r[4]))
    return rows, src_sha, len(data)


def build_matrix(rows):
    X, y, mats, envs, srcs, has_comp = [], [], [], [], [], 0
    for mat, env, temp, ly, source in rows:
        cv, ok = comp_vector(mat)
        has_comp += int(ok)
        ev = env_features(env)
        tnum = float(temp) if temp is not None else float("nan")
        tmiss = 0.0 if temp is not None else 1.0
        X.append(cv + ev + [tnum, tmiss])
        y.append(ly)
        mats.append(mat)
        envs.append(env)
        srcs.append(source)
    return (np.array(X, dtype=float), np.array(y, dtype=float),
            np.array(mats), np.array(envs), np.array(srcs), has_comp)


def metrics(y_true, y_pred):
    err = y_pred - y_true
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    ss_res = float(np.sum(err ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return rmse, mae, r2


_FAMILY_RULES = [
    ("copper_alloy", ["nickel-silver", "nickel silver", "cupronickel",
                       "copper-nickel", "copper nickel", "copper-zinc",
                       "copper zinc", "copper-tin", "copper-aluminum",
                       "copper-silicon"]),
    ("nickel_alloy", ["hastelloy"]),
    ("cobalt_alloy", ["haynes", "stellite", "mp35n", "co-cr", "co-20cr"]),
    ("carbide_cermet", ["wc-", "tac-"]),
    ("nickel_alloy", ["inconel", "incoloy", "monel", "duranickel", "nimonic",
                       "cabot", "illium", "worthite", "durimet", "chlorimet",
                       "durichlor", "durachlor", "carpenter 20", "carpenter20",
                       "20cb", "20 cb", "alloy 20", "nickel alloy",
                       "nickel  alloy"]),
    ("nickel_alloy", [r"\balloy\s*6\d\d\b", r"\balloy\s*8\d\d\b",
                       r"\b6\d\d\b.*inco", r"\b8\d\d\b.*inco",
                       "alloy c-", "alloy b-", "alloy g-", "alloy g\b",
                       "alloy d\b", "alloy s\b", "alloy x\b",
                       "nickel c-", "nickel b-", "nickel g",
                       "nickel-al bronze"]),
    ("nickel_alloy", ["nickel"]),
    ("stainless_steel", [
        r"\b3\d\d\b", r"\b40\d\b", r"\b41\d\b", r"\b42\d\b", r"\b43\d\b",
        r"\b44\d\b", r"\b2205\b", r"\b2304\b", r"\b2507\b",
        "904l", "254 smo", "al-6xn", "al 6xn", "al29-4", "al 29-4",
        "e-brite", "ferralium", "sanicro", "remanit", "26-1", "18-8",
        "cf-8", "cn-7m", "cd-4mcu", "cw-12m", "aci c", "duplex",
        "22cr-13ni", "21cr-6", "18cr-", "13cr", "12cr", "14cr", "9cr",
        "7cr", "5cr", "10cr", "17cr", "27cr", "29cr", "18.5%cr",
        "18cr", "1.25cr-0.5mo", "2.6cr", "5cr-1.5mo", "5cr-mo",
        "16ni, 8cr", "16ni,8cr", "25cr-22ni", "21cr-4ni", "2mo-0.4cu",
    ]),
    ("carbon_steel_cast_iron", [
        "steel", "cast iron", "ductile iron", "ni-resist", "armco iron",
        "white iron", "wrought iron", r"\ba\d\d\d\b", r"\b10\d\d\b",
        r"\b40\d\d\b", "api n", "1.2mn", "1.8ni-0.81cu", "3% nickel-iron",
        "hy-80",
    ]),
    ("copper_alloy", [
        "copper", "brass", "bronze", "admiralty", "ampco", "muntz",
        r"\bc\d{5}\b", "dhp", "ofe", "ofhc", "nickel bronze",
        "nickel- silver", "hydraulic bronze", "g bronze",
    ]),
    ("titanium", ["titanium", r"\bti-", "b/c titanium", "b/c-titanium",
                   "pure ti\b"]),
    ("zirconium_hafnium", ["zr7", "zr70", "zircaloy", "zirconium", "hf-",
                             "zr7o2"]),
    ("tantalum_niobium", ["tantalum", "niobium", "columbium", "cb alloy",
                            r"\bcb\b", "ta-mo", "cb-"]),
    ("precious_metal", ["platinum", "platnium", "silver", "gold", "rhodium",
                          "iridium", "ruthenium", "osmium", "palladium"]),
    ("lead", ["lead", "babbitt", "solder"]),
    ("magnesium", ["magnesium", r"\baz\d\d", "hk31a", "hm21a", "zk60a",
                    r"\bm1a\b"]),
    ("aluminum", ["aluminum", "alclad", r"\b[1-8]\d\d\d-", r"\b[1-8]\d\d\d\b",
                   "fecralloy", "al-3mg", "al-1mn"]),
    ("molybdenum", ["molybdenum"]),
    ("chromium", ["chromium", r"\bfe-47cr\b"]),
    ("tin", [r"\btin\b", "tin brass", "tin \\("]),
    ("zinc", ["zinc"]),
]
_COMPILED = []
for fam, pats in _FAMILY_RULES:
    for p in pats:
        _COMPILED.append((fam, re.compile(p)))


def classify_family(material):
    m = material.lower()
    for fam, rx in _COMPILED:
        if rx.search(m):
            return fam
    return None


def rnd(o):
    if isinstance(o, float):
        if math.isnan(o):
            return None
        return round(o, NDEC)
    if isinstance(o, dict):
        return {k: rnd(o[k]) for k in sorted(o)}
    if isinstance(o, list):
        return [rnd(v) for v in o]
    return o


def run_loso(Xc, yc, srcc, min_eligible_n=MIN_ELIGIBLE_N, seed=SEED):
    uniq_sources = sorted(set(srcc.tolist()))
    n_sources = len(uniq_sources)
    splitter = GroupKFold(n_splits=n_sources)
    it = list(splitter.split(Xc, yc, groups=srcc))
    assert len(it) == n_sources

    oof_pred = np.full(len(yc), np.nan)
    per_source = []
    for tr, te in it:
        src_here = sorted(set(srcc[te].tolist()))
        assert len(src_here) == 1, "LOSO fold leaked >1 source: %r" % src_here
        src_name = src_here[0]
        model = HistGradientBoostingRegressor(
            random_state=seed, max_iter=300, learning_rate=0.05,
            max_depth=None, max_leaf_nodes=31, l2_regularization=1.0,
            early_stopping=False)
        model.fit(Xc[tr], yc[tr])
        pred_te = model.predict(Xc[te])
        oof_pred[te] = pred_te
        rmse, mae, r2 = metrics(yc[te], pred_te)
        train_mean = float(np.mean(yc[tr]))
        base_rmse, _, _ = metrics(yc[te], np.full(len(te), train_mean))
        per_source.append({
            "source": src_name,
            "n_test": int(len(te)),
            "r2": r2,
            "rmse": rmse,
            "mae": mae,
            "baseline_global_mean_rmse": base_rmse,
            "beats_global_mean_baseline_rmse": bool(rmse < base_rmse),
        })
    per_source.sort(key=lambda d: -d["n_test"])
    overall_rmse, overall_mae, overall_r2 = metrics(yc, oof_pred)

    eligible = [d for d in per_source if d["n_test"] >= min_eligible_n]
    excluded = [d for d in per_source if d["n_test"] < min_eligible_n]
    n_eligible = len(eligible)
    source_weighted_mean_r2 = float(np.mean([d["r2"] for d in eligible])) if eligible else float("nan")
    n_eligible_positive = sum(1 for d in eligible if d["r2"] > 0.0)
    n_eligible_nonpositive = n_eligible - n_eligible_positive
    frac_eligible_positive = (n_eligible_positive / n_eligible) if n_eligible else float("nan")
    majority_positive = (n_eligible_positive > n_eligible / 2.0) if n_eligible else False
    refuted = (source_weighted_mean_r2 <= 0.0) or (not majority_positive)

    return {
        "n_sources": n_sources,
        "sample_weighted_oof": {"rmse": overall_rmse, "mae": overall_mae, "r2": overall_r2},
        "per_source_loso": per_source,
        "eligible_sources_n_test_ge_min": n_eligible,
        "excluded_sources_below_min_count": len(excluded),
        "source_weighted_mean_r2": source_weighted_mean_r2,
        "n_eligible_sources_r2_positive": n_eligible_positive,
        "n_eligible_sources_r2_nonpositive": n_eligible_nonpositive,
        "frac_eligible_sources_r2_positive": frac_eligible_positive,
        "majority_of_eligible_sources_positive": majority_positive,
        "refuted": refuted,
    }


def main():
    rows, src_sha, n_raw = load()
    X, y, mats, envs, srcs, has_comp = build_matrix(rows)

    fam_list = [classify_family(m) for m in mats]
    classified_mask = np.array([f is not None for f in fam_list])
    families_all = np.array([f if f is not None else "unclassified" for f in fam_list])

    Xc = X[classified_mask]
    yc = y[classified_mask]
    famc = families_all[classified_mask]
    srcc = srcs[classified_mask]
    n_c = len(yc)
    n_families = len(set(famc.tolist()))

    real = run_loso(Xc, yc, srcc)
    verdict = "CLAIM_REFUTED" if real["refuted"] else "CLAIM_SURVIVED"

    refutation_criterion = (
        "REFUTED if (a) source-count-weighted (unweighted-per-source) mean "
        "LOSO R2 over sources with n_test>=%d in the classified subset "
        "<= 0.0, OR (b) a majority (>50%%) of those eligible sources "
        "individually score LOSO R2 <= 0.0. SURVIVED if source-weighted "
        "mean R2 > 0.0 AND a majority of eligible sources individually "
        "score R2 > 0.0, even if reduced relative to the family-safe/LOFO "
        "numbers (some reduction from a different, potentially harder, "
        "axis is expected and is not itself a refutation)." % MIN_ELIGIBLE_N
    )

    canonical = {
        "schema": "amphora.barrier-corrosion-score.corr-rate-source-lofo-attack.v1",
        "benchmark": "amphora-barrier-corrosion-score/corr-rate-source-lofo-v1",
        "attacks_claim": (
            "evidence/phase0/kpis/corr-rate-family-safe-qspr-kpi.v1.dsse.json: "
            "GroupKFold(group=metallurgical_family, 5-fold) HistGBM R2=0.132087 "
            "on the NIST CORR-DATA classified subset (n=7282, 17 families), "
            "'the module's strongest rights-clean empirical claim'; and, by "
            "extension, corr-rate-family-lofo-v1's CLAIM_SURVIVED verdict "
            "(family-weighted mean R2=0.015964)."
        ),
        "attack_description": (
            "NIST CORR-DATA is a compilation of 220 distinct original "
            "literature sources (source_text field: corrosion handbooks, "
            "alloy-vendor bulletins, journal papers across decades). Most "
            "sources are family-specialized (e.g. Climax Molybdenum reports "
            "mostly molybdenum/nickel alloys; Haynes reports mostly cobalt/ "
            "nickel superalloys), so family-safe or per-family LOFO splits "
            "do not control for a model that has merely learned a source's "
            "own testing methodology / reporting convention rather than a "
            "transferable structure-composition-environment relationship. "
            "This re-runs the identical feature engineering, HistGBM model, "
            "and seed with true Leave-One-Source-Out (n_splits=n_sources in "
            "the classified subset, one source held out per fold) on the "
            "SAME classified cohort (n=7282, 17 families) used by the "
            "promoted KPI and corr-rate-family-lofo-v1, and reports the "
            "SOURCE-weighted (unweighted per source) mean R2 alongside the "
            "sample-weighted OOF R2."
        ),
        "refutation_criterion": refutation_criterion,
        "min_eligible_n_test": MIN_ELIGIBLE_N,
        "dataset": {
            "name": "NIST CORR-DATA (Dow Chemical Co.) derived reference",
            "in_tree_path": SRC,
            "source_sha256": src_sha,
            "rights_class": "DERIVATIVE_ALLOWED",
            "n_raw_records": n_raw,
        },
        "cohort": {
            "classified_subset_n": n_c,
            "n_families": n_families,
            "n_sources_in_classified_subset": real["n_sources"],
        },
        "results": {
            "sample_weighted_oof": real["sample_weighted_oof"],
            "per_source_loso": real["per_source_loso"],
            "eligible_sources_n_test_ge_min": real["eligible_sources_n_test_ge_min"],
            "excluded_sources_below_min_count": real["excluded_sources_below_min_count"],
            "source_weighted_mean_r2": real["source_weighted_mean_r2"],
            "n_eligible_sources_r2_positive": real["n_eligible_sources_r2_positive"],
            "n_eligible_sources_r2_nonpositive": real["n_eligible_sources_r2_nonpositive"],
            "frac_eligible_sources_r2_positive": real["frac_eligible_sources_r2_positive"],
            "majority_of_eligible_sources_positive": real["majority_of_eligible_sources_positive"],
        },
        "comparison_to_promoted_kpi": {
            "kpi_sample_weighted_5fold_family_safe_r2": 0.132087,
            "family_lofo_family_weighted_mean_r2": 0.015964,
            "loso_sample_weighted_oof_r2": real["sample_weighted_oof"]["r2"],
            "loso_source_weighted_mean_r2": real["source_weighted_mean_r2"],
            "note": (
                "kpi number is sample-weighted, 5-fold, grouped by "
                "metallurgical family; loso_sample_weighted_oof_r2 is the "
                "directly comparable per-row OOF statistic under true "
                "source-grouped LOSO; loso_source_weighted_mean_r2 treats "
                "every literature source as one equally-weighted unit -- "
                "the honest reading of whether the model transfers across "
                "independent data-collection provenance, not just across "
                "metallurgical families that happen to share a source."
            ),
        },
        "verdict": verdict,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "modifies_manifest": False,
        "scope_honesty": (
            "Diagnostic on bare metal/alloy substrate corrosion (NIST "
            "CORR-DATA), same scope ceiling as corr-rate-qspr-v1 and "
            "corr-rate-family-safe-v1: NOT organic-coating barrier "
            "performance. No candidate/coating superiority claim."
        ),
        "model": {
            "estimator": "HistGradientBoostingRegressor",
            "params": {"max_iter": 300, "learning_rate": 0.05,
                       "max_leaf_nodes": 31, "l2_regularization": 1.0,
                       "random_state": SEED},
            "sklearn_version": sklearn.__version__,
        },
        "determinism": {"omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
                        "seed": SEED, "canonical_round_decimals": NDEC},
    }
    out = json.dumps(rnd(canonical), indent=2, sort_keys=True)
    open(sys.argv[1] if len(sys.argv) > 1 else "result.json", "w").write(out)
    sha = hashlib.sha256(out.encode()).hexdigest()
    print("CANONICAL_SHA256", sha)
    print("n_sources", real["n_sources"], "n_eligible", real["eligible_sources_n_test_ge_min"])
    print("sample_weighted_oof_r2", round(real["sample_weighted_oof"]["r2"], 4))
    print("source_weighted_mean_r2", round(real["source_weighted_mean_r2"], 4))
    print("n_eligible_positive", real["n_eligible_sources_r2_positive"], "/", real["eligible_sources_n_test_ge_min"])
    print("verdict", verdict)


if __name__ == "__main__":
    main()
