#!/usr/bin/env python3
"""R-B03: run the corrected flory-hansen-corrected-v1 instrument on a
deterministic sample (seed 0, n=2500) of the OMG corpus the refuted KPIs used.

Corpus: feedback/v3/normalized/omg_physical_properties_v3.jsonl.gz
  (dataset_id omg_physical_properties_v3-3e5af76bc6a1f8ea, raw zip sha256
  3e5af76b... == input_zip_sha256 of BOTH refuted receipts).
Rights lock verified BEFORE opening: manifests/omg_physical_properties_v3.json
  rights_class=DERIVATIVE_ALLOWED, quarantined=false.

Selection (fully deterministic):
  1. stream records; keep raw_fields.methyl_terminated_product where all
     three chi_parameter_{chloroform,ethanol,water}_mean fields are present
     (the chi corpus the KPIs consumed; SMILES column methyl_terminated_product,
     the same column W7 identified);
  2. unique SMILES strings, sorted();
  3. random.Random(0).sample(sorted_list, 2500).

Outputs canonical JSON (sort_keys, compact separators). Run twice by the
wrapper for the two-replay byte-identity gate.
"""
import gzip
import hashlib
import json
import random
import statistics
import sys

sys.path.insert(0, "/home/ubuntu/amphora/build/mvp20-split/amphora-solvency-score/benchmarks/flory-hansen-corrected-v1")
import compute_group_contribution as gc

CORPUS = "/home/ubuntu/amphora/build/mvp20-split/feedback/v3/normalized/omg_physical_properties_v3.jsonl.gz"
MANIFEST = "/home/ubuntu/amphora/build/mvp20-split/amphora-solvency-score/reference/mvp20/data/feedback_v3/manifests/omg_physical_properties_v3.json"
SEED = 0
N_SAMPLE = 2500
CHI_FIELDS = ("chi_parameter_chloroform_mean", "chi_parameter_ethanol_mean",
              "chi_parameter_water_mean")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sample():
    man = json.load(open(MANIFEST))
    assert man["rights_class"] == "DERIVATIVE_ALLOWED", "rights lock not clean"
    assert man["quarantined"] is False, "corpus quarantined"
    corpus_sha = sha256_file(CORPUS)
    assert corpus_sha == man["normalized_sha256"], (
        "corpus bytes do not match manifest lock: %s" % corpus_sha)
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
    return {
        "corpus_path": CORPUS,
        "corpus_sha256": corpus_sha,
        "manifest_rights_class": man["rights_class"],
        "manifest_quarantined": man["quarantined"],
        "dataset_id": man["dataset_id"],
        "n_records_streamed": n_records,
        "n_chi_records": n_chi_records,
        "n_unique_smiles": len(pool),
        "seed": SEED,
        "n_sample": N_SAMPLE,
    }, sample


def stats_over(vals):
    if not vals:
        return None
    v = sorted(vals)
    return {
        "n": len(v),
        "min": v[0],
        "median": statistics.median(v),
        "mean": statistics.fmean(v),
        "max": v[-1],
    }


def main(out_path):
    prov, sample = load_sample()
    results = [gc.compute(s) for s in sample]

    per_quantity = {}
    for q in ("fedors_delta_total", "hansen_delta_d", "hansen_delta_p",
              "hansen_delta_h", "hansen_delta_total"):
        per_quantity[q] = stats_over(
            [r["values"][q] for r in results if q in r["values"]])

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
        c["identity_returned_plus_abstained_plus_rejected"] = (
            c["RETURNED"] + c["ABSTAINED"] + c["REJECTED"])
        c["identity_equals_n_sample"] = (
            c["identity_returned_plus_abstained_plus_rejected"] == len(results))
        c["abstention_rate"] = c["ABSTAINED"] / len(results)
        c["rejection_rate"] = c["REJECTED"] / len(results)
        c["return_rate"] = c["RETURNED"] / len(results)
        return c

    # in-envelope assertion over every RETURNED value
    violations = []
    for r in results:
        for q, val in r["values"].items():
            if q in ("fedors_delta_total", "hansen_delta_total", "hansen_delta_d"):
                ok = gc.ENVELOPE_MIN <= val <= gc.ENVELOPE_MAX
            else:
                ok = 0.0 <= val <= gc.ENVELOPE_MAX
            if not ok:
                violations.append({"smiles": r["smiles"], "q": q, "val": val})
    assert not violations, "out-of-envelope value RETURNED: %r" % violations[:3]

    diag = {
        "schema": "amphora.solvency-score.flory-hansen-corrected-omg-sample-diagnostic.v1",
        "repair_item": "R-B03",
        "provenance": prov,
        "envelope_MPa_half": [gc.ENVELOPE_MIN, gc.ENVELOPE_MAX],
        "envelope_application": {
            "fedors_delta_total": "two-sided [9.6, 59.875]",
            "hansen_delta_total": "two-sided [9.6, 59.875]",
            "hansen_delta_d": "two-sided [9.6, 59.875]",
            "hansen_delta_p": "one-sided [0, 59.875]",
            "hansen_delta_h": "one-sided [0, 59.875]",
        },
        "accounting": {"fedors": account("fedors"), "hansen": account("hansen")},
        "distribution_MPa_half": per_quantity,
        "out_of_envelope_returns": 0,
        "per_molecule": [
            {"smiles": r["smiles"],
             "fedors_status": r["fedors_status"],
             "hansen_status": r["hansen_status"],
             "values": r["values"]}
            for r in results
        ],
    }
    blob = gc.canonical_json(diag).encode()
    with open(out_path, "wb") as f:
        f.write(blob)
    print(out_path, hashlib.sha256(blob).hexdigest())


if __name__ == "__main__":
    main(sys.argv[1])
