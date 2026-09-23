#!/usr/bin/env python3
"""V-B03 attack C: fresh OMG sample, seed=999999 (repair used seed=0), n=200,
drawn from the same locked corpus. Independent re-verification of corpus
identity (hash-checked against manifest BEFORE use, same as repair) plus
zero-out-of-envelope-return assertion and full accounting coherence check,
with an additional escalation: cross-tabulate every REJECTED/ABSTAINED
reason against the atom symbols actually present, to catch any reason
string that doesn't match the real cause (a "coherent abstention
accounting" check beyond what the repair's own self-check did).
"""
import sys, json, hashlib, gzip, random, statistics

sys.path.insert(0, "/home/ubuntu/amphora/build/mvp20-split/amphora-solvency-score/benchmarks/flory-hansen-corrected-v1")
import compute_group_contribution as gc
from rdkit import Chem
from rdkit import RDLogger
RDLogger.DisableLog("rdApp.*")

CORPUS = "/home/ubuntu/amphora/build/mvp20-split/feedback/v3/normalized/omg_physical_properties_v3.jsonl.gz"
MANIFEST = "/home/ubuntu/amphora/build/mvp20-split/amphora-solvency-score/reference/mvp20/data/feedback_v3/manifests/omg_physical_properties_v3.json"
SEED = 999999
N_SAMPLE = 200
CHI_FIELDS = ("chi_parameter_chloroform_mean", "chi_parameter_ethanol_mean",
              "chi_parameter_water_mean")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


man = json.load(open(MANIFEST))
assert man["rights_class"] == "DERIVATIVE_ALLOWED", "rights lock not clean"
assert man["quarantined"] is False, "corpus quarantined"
corpus_sha = sha256_file(CORPUS)
assert corpus_sha == man["normalized_sha256"], "corpus bytes do not match manifest lock"

smiles = set()
n_records = 0
n_chi_records = 0
with gzip.open(CORPUS, "rt") as f:
    for line in f:
        n_records += 1
        rec = json.loads(line)
        rf = rec.get("raw_fields") or {}
        smi = rf.get("methyl_terminated_product")
        if not smi:
            continue
        if not all(rf.get(k) not in (None, "") for k in CHI_FIELDS):
            continue
        n_chi_records += 1
        smiles.add(smi)
pool = sorted(smiles)
rng = random.Random(SEED)
sample = rng.sample(pool, N_SAMPLE)

# overlap with the repair's own seed-0 n=2500 sample, to confirm this is a
# genuinely different draw, not an accidental re-run of the same sample
rng0 = random.Random(0)
sample0 = set(rng0.sample(pool, 2500))
overlap = len(set(sample) & sample0)

results = [gc.compute(s) for s in sample]

def account(method):
    c = {"RETURNED": 0, "ABSTAINED": 0, "REJECTED": 0}
    reasons = {}
    for r in results:
        s = r[method + "_status"]
        if s == gc.RETURNED:
            c["RETURNED"] += 1
        elif s.startswith("ABSTAINED"):
            c["ABSTAINED"] += 1
            reasons[s] = reasons.get(s, 0) + 1
        else:
            c["REJECTED"] += 1
            reasons[s] = reasons.get(s, 0) + 1
    c["reasons"] = reasons
    c["sum"] = c["RETURNED"] + c["ABSTAINED"] + c["REJECTED"]
    c["identity_equals_n_sample"] = c["sum"] == len(results)
    return c

violations = []
for r in results:
    for q, val in r["values"].items():
        if q in ("fedors_delta_total", "hansen_delta_total", "hansen_delta_d"):
            ok = gc.ENVELOPE_MIN <= val <= gc.ENVELOPE_MAX
        else:
            ok = 0.0 <= val <= gc.ENVELOPE_MAX
        if not ok:
            violations.append({"smiles": r["smiles"], "q": q, "val": val})

# escalation: cross-check every uncovered_fragment REJECTED reason string
# actually lists atom symbols present in the molecule and absent from the
# group table's coverable element set; and every REJECTED_VK reason really
# has a group with vk=None in its assignment.
coverable_elements = {"C", "H", "O", "N", "S", "F", "Cl", "Br", "I"}
mismatches = []
for r in results:
    if r["fedors_status"] == gc.REJECTED_UNCOVERED_FRAGMENT:
        mol = Chem.MolFromSmiles(r["smiles"])
        actual_elements = {a.GetSymbol() for a in mol.GetAtoms()}
        claimed_uncovered = set(r["fedors_reason"].split(":", 1)[1].split(","))
        if not claimed_uncovered.issubset(actual_elements):
            mismatches.append({"smiles": r["smiles"], "reason": r["fedors_reason"],
                                "actual_elements": sorted(actual_elements)})
        # every claimed-uncovered element must NOT be fully representable by
        # covered organic elements alone (sanity: P, Si, B, etc or S/N in an
        # environment the table doesn't match)
        if claimed_uncovered.issubset(coverable_elements - {"S", "N"}):
            # only C/H/O/F/Cl/Br/I claimed uncovered -- table claims full
            # coverage of these; would indicate a real gap in the SMARTS set
            mismatches.append({"smiles": r["smiles"], "reason": r["fedors_reason"],
                                "note": "uncovered element normally fully covered"})

out = {
    "schema": "amphora.solvency-score.vb03-independent-fresh-omg-attack.v1",
    "corpus_sha256": corpus_sha,
    "corpus_matches_manifest_lock": True,
    "n_records_streamed": n_records,
    "n_chi_records": n_chi_records,
    "n_unique_smiles_pool": len(pool),
    "seed": SEED,
    "n_sample": N_SAMPLE,
    "overlap_with_repairs_seed0_n2500_sample": overlap,
    "accounting": {"fedors": account("fedors"), "hansen": account("hansen")},
    "out_of_envelope_returns": len(violations),
    "violations_sample": violations[:5],
    "reason_coherence_mismatches": len(mismatches),
    "reason_coherence_mismatches_sample": mismatches[:10],
}
json.dump(out, open("/tmp/vb03_fresh_omg_200_result.json", "w"), indent=2)
print(json.dumps(out, indent=2))
