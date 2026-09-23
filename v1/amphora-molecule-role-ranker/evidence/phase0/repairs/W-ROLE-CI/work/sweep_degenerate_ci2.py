import json, os, re

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
KEY_PAT = re.compile(r"ci|interval|bound|coverage", re.IGNORECASE)
OUT = "/home/ubuntu/amphora/build/mvp20-split/amphora-molecule-role-ranker/evidence/phase0/repairs/W-ROLE-CI/work/sweep_results.json"

hits = []
n_scanned = 0
n_parsed = 0
errors = 0


def walk(obj, path, filepath):
    if isinstance(obj, dict):
        for k, v in obj.items():
            newpath = f"{path}.{k}" if path else k
            if isinstance(v, list) and len(v) == 2 and KEY_PAT.search(k):
                a, b = v[0], v[1]
                if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
                    if (a == 0.0 and b == 0.0) or (a == 1.0 and b == 1.0):
                        hits.append((filepath, newpath, [a, b]))
            walk(v, newpath, filepath)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]", filepath)


for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", "target", "node_modules")]
    for fn in filenames:
        if not fn.endswith(".json"):
            continue
        fp = os.path.join(dirpath, fn)
        n_scanned += 1
        try:
            with open(fp, "r") as f:
                data = json.load(f)
        except Exception:
            errors += 1
            continue
        n_parsed += 1
        walk(data, "", fp)

by_module = {}
for fp, path, v in hits:
    rel = os.path.relpath(fp, ROOT)
    module = rel.split("/")[0]
    by_module.setdefault(module, []).append({"path": rel, "field": path, "value": v})

# collapse to one representative entry per (module, dirname-stripped-basename-pattern)
distinct_outside = []
for module, entries in sorted(by_module.items()):
    if module == "amphora-molecule-role-ranker":
        continue
    # group by the artifact directory (strip diagnostic.canonical vs runB duplication)
    seen_dirs = {}
    for e in entries:
        d = os.path.dirname(e["path"])
        seen_dirs.setdefault(d, []).append(e)
    distinct_outside.append({
        "module": module,
        "n_hits_total": len(entries),
        "distinct_artifact_dirs": sorted(seen_dirs.keys()),
        "sample_fields": sorted({e["field"] for e in entries})[:10],
    })

result = {
    "n_json_files_found": n_scanned,
    "n_json_files_parsed": n_parsed,
    "n_parse_errors": errors,
    "n_degenerate_hits": len(hits),
    "distinct_artifacts_outside_this_module": distinct_outside,
}
with open(OUT, "w") as f:
    json.dump(result, f, indent=2, sort_keys=True)
print(json.dumps(result, indent=2))
