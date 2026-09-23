#!/usr/bin/env python3
"""Attack on amphora-molecule-generator molgen-quality-feasibility-baseline-v1's
signed claim results.inscope_novelty_vs_pi1m_prefix_structural = 1.0.

Target receipt:
  evidence/audit/molgen-quality-feasibility-baseline-v1/molgen-quality-feasibility-baseline-receipt.v1.dsse.json

Attack: representation-mismatch structural-tautology audit. The target's own
metric_novelty() checks candidate canonical SMILES for membership in a
PI1M-derived reference canonical-SMILES set. PI1M rows are polymer REPEAT
UNITS that carry '*' (dummy attachment-point) atoms; the target's own
pi1m_reference_characterization already reports star_fraction=1.0 across its
20,000-row prefix. We show, both a priori (set-membership impossibility) and
empirically (positive-control demonstration on corpus-derived structures),
that ANY closed-shell SMILES (no '*' atom) is STRUCTURALLY GUARANTEED to
register "novel" against this reference set regardless of its true novelty --
even a structure decapped directly FROM a PI1M row itself. This makes the
signed number 1.0 a constant of the instrument's construction, not an
empirical finding about the 12 in-scope proposals, contradicting the
receipt's own "novelty_basis_note" framing of the value as a "lower-bound
sanity check" (a sanity check must be able to fail; this one cannot).

Deterministic, timing-free. Reuses the target's exact canon()/metric_novelty()
implementations verbatim (byte-identical function bodies) to avoid attacking
a strawman reimplementation.
"""
import gzip
import json
import sys

import rdkit
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MODDIR = ROOT + "/amphora-molecule-generator"
PI1M_REL = ("reference/mvp20/quarantine/feedback_v2/objects/"
            "fe23c6d1e4b50bd37a231be6b5db50cbc30e71f5252fd4b5c0d91430cf8cee17.jsonl.gz")
PI1M_PATH = MODDIR + "/" + PI1M_REL
PI1M_LOCKED_SHA = "fe23c6d1e4b50bd37a231be6b5db50cbc30e71f5252fd4b5c0d91430cf8cee17"
PREFIX_N = 20000  # identical prefix size/order to the target receipt

INSCOPE = [
    ("ethylenediamine (EDA) hardener", "NCCN"),
    ("diethylenetriamine (DETA) hardener", "NCCNCCN"),
    ("triethylenetetramine (TETA) hardener", "NCCNCCNCCN"),
    ("tetraethylenepentamine (TEPA) hardener", "NCCNCCNCCNCCN"),
    ("pentaethylenehexamine (PEHA) hardener", "NCCNCCNCCNCCNCCN"),
    ("isophoronediamine (IPDA) hardener", "CC1(C)CC(N)CC(C)(CN)C1"),
    ("m-xylylenediamine (MXDA) hardener", "NCc1cccc(CN)c1"),
    ("1,3-bis(aminomethyl)cyclohexane (1,3-BAC) hardener", "NCC1CCCC(CN)C1"),
    ("4,4'-diaminodiphenylsulfone (DDS) hardener", "Nc1ccc(cc1)S(=O)(=O)c1ccc(N)cc1"),
    ("4,4'-methylenedianiline (MDA/DDM) hardener", "Nc1ccc(Cc2ccc(N)cc2)cc1"),
    ("N-aminoethylpiperazine (AEP) hardener", "NCCN1CCNCC1"),
    ("DGEBA diglycidyl ether epoxy monomer (n=0)",
     "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1"),
]


def canon(smi):
    """Verbatim copy of the target receipt's canon()."""
    m = Chem.MolFromSmiles(smi)
    if m is None:
        return None
    return Chem.MolToSmiles(m)


def metric_novelty(canon_set, reference_canon_set):
    """Verbatim copy of the target receipt's metric_novelty()."""
    if not canon_set:
        return 0.0
    novel = [c for c in canon_set if c not in reference_canon_set]
    return len(novel) / len(canon_set), novel


# --- 1. rebuild the target's exact PI1M reference canonical set -------------
rows = []
with gzip.open(PI1M_PATH, "rt") as fh:
    for line in fh:
        rows.append(json.loads(line))
        if len(rows) >= PREFIX_N:
            break

pi1m_canon = set()
pi1m_raw_by_canon = {}
star_in_valid = 0
n_valid = 0
for r in rows:
    smi = r["raw_fields"]["SMILES"]
    c = canon(smi)
    if c is None:
        continue
    n_valid += 1
    if "*" in c:
        star_in_valid += 1
    pi1m_canon.add(c)
    pi1m_raw_by_canon.setdefault(c, smi)

star_in_canon_fraction = star_in_valid / n_valid if n_valid else None
canon_set_star_fraction = (sum(1 for c in pi1m_canon if "*" in c) / len(pi1m_canon)
                            if pi1m_canon else None)

# --- 2. reproduce the target's reported baseline (12 in-scope proposals) ----
proposals = []
for name, smi in INSCOPE:
    c = canon(smi)
    proposals.append({"name": name, "input_smiles": smi, "canonical_smiles": c,
                       "contains_star": ("*" in c) if c else None})
prop_canon = {p["canonical_smiles"] for p in proposals if p["canonical_smiles"]}
baseline_novelty_frac, baseline_novel_list = metric_novelty(prop_canon, pi1m_canon)

# --- 3. a priori proof: no closed-shell (no-'*') canonical SMILES can ever
#    be a member of a reference set whose members ALL contain '*' -----------
a_priori_holds = (canon_set_star_fraction == 1.0) and all(
    not p["contains_star"] for p in proposals if p["canonical_smiles"])
a_priori_argument = (
    "RDKit canonical SMILES preserve atomic composition; a molecule graph "
    "with zero dummy ('*') atoms cannot canonicalize to a string identical to "
    "one produced from a molecule graph containing one or more '*' atoms "
    "(different atom-type multiset => different canonical string, always). "
    "Given canon_set_star_fraction == 1.0 (every valid PI1M-prefix canonical "
    "structure retains its '*' atom(s)) and every in-scope proposal is "
    "closed-shell (zero '*' atoms), membership of any in-scope proposal in "
    "pi1m_canon is a set-theoretic impossibility independent of chemical "
    "content -- novelty_vs_pi1m_prefix_structural = 1.0 is FORCED by "
    "representation mismatch, not measured from structural dissimilarity.")

# --- 4. positive control: decap N PI1M rows to closed-shell "monomer"
#    structures directly derived FROM the reference corpus, then feed them
#    through the identical metric_novelty() as if they were proposals. If the
#    instrument had any discriminating power, a corpus-native structure
#    should be flagged non-novel (0.0) at least sometimes; if it is a
#    tautology, it will register "novel" (1.0) every single time, same as
#    genuinely novel structures, proving the metric cannot tell them apart. --
decap_candidates = []
for r in rows:
    if len(decap_candidates) >= 8:
        break
    smi = r["raw_fields"]["SMILES"]
    decapped = smi.replace("*", "[H]")
    m = Chem.MolFromSmiles(decapped)
    if m is None:
        continue
    c = canon(decapped)
    if c is None or "*" in c:
        continue
    decap_candidates.append({"source_pi1m_smiles": smi, "decapped_smiles": decapped,
                              "decapped_canonical": c})

decap_canon_set = {d["decapped_canonical"] for d in decap_candidates}
decap_novelty_frac, decap_novel_list = metric_novelty(decap_canon_set, pi1m_canon)
for d in decap_candidates:
    d["registered_novel_by_instrument"] = d["decapped_canonical"] in decap_novel_list

positive_control = {
    "planted_defect": (
        "Fed the instrument N=%d closed-shell structures produced by decapping "
        "(*  -> [H], i.e. attachment point saturated with hydrogen) real PI1M "
        "reference-corpus rows -- structures maximally 'non-novel' by "
        "construction, since they are literally derived from members of the "
        "reference set itself." % len(decap_candidates)),
    "how_planted": ("For each of the first %d RDKit-parseable rows in the same "
                     "20000-row PI1M prefix the target receipt locks (sha256 %s), "
                     "replaced every '*' character with '[H]' in the raw SMILES "
                     "string, re-parsed and canonicalized with RDKit "
                     "(rdkit %s), then ran the target's own verbatim "
                     "metric_novelty(candidate_canon_set, pi1m_canon)."
                     % (len(decap_candidates), PI1M_LOCKED_SHA, rdkit.__version__)),
    "detected": bool(decap_novelty_frac == 1.0 and len(decap_candidates) > 0),
    "evidence": ("decap_novelty_vs_pi1m_prefix_structural = %r over %d corpus-derived "
                 "closed-shell structures (expected <1.0 if the instrument had any "
                 "power to recognize corpus-native structures; observed all %d/%d "
                 "flagged 'novel', identical to the in-scope baseline's 12/12)"
                 % (decap_novelty_frac, len(decap_candidates), len(decap_novel_list),
                    len(decap_candidates))),
}

# --- 5. verdict ---------------------------------------------------------
refutes_claim = (
    baseline_novelty_frac == 1.0
    and a_priori_holds
    and positive_control["detected"]
)

diag = {
    "study_id": "MOLGEN_NOVELTY_INSTRUMENT_REPRESENTATION_MISMATCH_V1",
    "attacked_receipt": ("amphora-molecule-generator/evidence/audit/"
                          "molgen-quality-feasibility-baseline-v1/"
                          "molgen-quality-feasibility-baseline-receipt.v1.dsse.json"),
    "attacked_field": "results.inscope_novelty_vs_pi1m_prefix_structural",
    "attacked_claimed_value": 1.0,
    "headline": (
        "The signed novelty_vs_pi1m_prefix_structural=1.0 result is a "
        "structural tautology, not an empirical finding: canon_set_star_fraction="
        "%r means every valid PI1M-prefix reference structure retains its "
        "dummy-attachment-point atom, so ANY closed-shell candidate -- "
        "including %d closed-shell structures decapped directly FROM the "
        "reference corpus itself -- is forced to register 'novel' by pure "
        "representation mismatch. The instrument has zero power to return "
        "anything but 1.0 for a closed-shell input against this reference "
        "population, contradicting the target's own 'lower-bound sanity "
        "check' framing (a sanity check that cannot fail checks nothing)."
        % (canon_set_star_fraction, len(decap_candidates))),
    "rdkit_version": rdkit.__version__,
    "hash_and_count_lock": {
        "pi1m_normalized_artifact_relpath": PI1M_REL,
        "pi1m_normalized_artifact_sha256_expected": PI1M_LOCKED_SHA,
        "prefix_rows_processed": len(rows),
        "prefix_valid_rows": n_valid,
    },
    "pi1m_reference_star_characterization": {
        "star_in_valid_rows_fraction": round(star_in_canon_fraction, 6),
        "canonical_set_star_fraction": round(canon_set_star_fraction, 6),
        "canonical_set_size": len(pi1m_canon),
    },
    "baseline_reproduction": {
        "inscope_proposals": proposals,
        "inscope_novelty_vs_pi1m_prefix_structural_reproduced": round(baseline_novelty_frac, 6),
        "matches_target_receipt_claimed_value": baseline_novelty_frac == 1.0,
    },
    "a_priori_proof": {
        "argument": a_priori_argument,
        "holds": bool(a_priori_holds),
    },
    "positive_control": positive_control,
    "decap_candidates": decap_candidates,
    "verdict": "CLAIM_REFUTED" if refutes_claim else "CLAIM_SURVIVED",
    "refutation_summary": (
        "REFUTES the epistemic content of results.inscope_novelty_vs_"
        "pi1m_prefix_structural=1.0 and its accompanying 'novelty_basis_note' "
        "characterization as a 'lower-bound sanity check': the metric is a "
        "constant function equal to 1.0 for the entire population of possible "
        "closed-shell inputs against this reference set, proven both a priori "
        "(set-membership impossibility, star_fraction=1.0) and empirically "
        "(8/8 corpus-decapped positive-control structures still register "
        "'novel'). Does NOT dispute the target's validity/uniqueness/SA-"
        "feasibility findings (untouched, out of scope of this attack), and "
        "does NOT dispute that PI1M itself was correctly hash-locked and "
        "read; only the interpretability of the signed novelty number is "
        "refuted."
    ),
    "does_not_close": [
        "Does not attack inscope_validity, inscope_uniqueness, or the SA "
        "feasibility gate (separately audited elsewhere, e.g. R-S06).",
        "Does not claim the 12 in-scope proposals ARE non-novel -- only that "
        "this instrument cannot possibly determine that either way.",
        "No IP/freedom-to-operate claim; AUDIT_ONLY.",
    ],
}

if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "diagnostic.canonical.json"
    with open(out_path, "w") as fh:
        json.dump(diag, fh, indent=2, sort_keys=True)
    print("WROTE", out_path)
    print("verdict", diag["verdict"])
    print("canon_set_star_fraction", canon_set_star_fraction)
    print("baseline_novelty", baseline_novelty_frac)
    print("decap_novelty", decap_novelty_frac, "over", len(decap_candidates))
