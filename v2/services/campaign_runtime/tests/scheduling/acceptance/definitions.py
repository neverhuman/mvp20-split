"""Synthetic graph inputs assembled from preserved wire fixtures and actual public tool pins."""

import copy
import json
from pathlib import Path


def configure(e):
    root = Path(__file__).absolute().parents[5]
    cases = json.loads((root / "contracts/fixtures/v2/executable_cases.json").read_bytes())
    definitions = [copy.deepcopy(case["payload"]) for case in cases if case["valid"] and case["model"] == "campaigns.definition"]
    numeric, sequence = e.tools
    assert numeric.module == "amphora_numeric_affine" and sequence.module == "amphora_sequence_statistics"
    for value in definitions:
        value["scope"] = e.scope
    branch = definitions[1]
    branch["body"]["inputs"] = branch["body"]["inputs"][:1]
    branch["body"]["nodes"][0]["predicate"] = {"kind": "compare", "left": {
        "source": {"kind": "input", "name": "parameters"}, "path": ["a"],
        "value_type": {"kind": "scalar", "scalar": "number", "unit": "1"}},
        "operator": "eq", "right": {"kind": "number", "value": numeric.image["golden_input"]["a"], "unit": "1"}}
    loop_graph = definitions[3]
    loop = loop_graph["body"]["nodes"][0]
    loop_graph["body"]["inputs"] = copy.deepcopy(definitions[0]["body"]["inputs"])
    loop["captures"] = [{"port": "parameters", "source": {"kind": "input", "name": "parameters"}}]
    loop["body"]["inputs"].extend(copy.deepcopy(loop_graph["body"]["inputs"]))
    invoke = copy.deepcopy(definitions[0]["body"]["nodes"][0])
    invoke["node_id"] = "map"
    finish = loop["body"]["nodes"][0]
    finish["outputs"].append({"port": "result", "source": {"kind": "output", "node_id": "map", "port": "result"}})
    loop["body"]["nodes"] = [invoke, finish]
    loop["body"]["edges"] = [{"source": "map", "target": "finish", "route": "next"}]
    loop["body"]["outputs"].extend(copy.deepcopy(definitions[0]["body"]["outputs"]))
    loop_graph["body"]["outputs"].extend(copy.deepcopy(definitions[0]["body"]["outputs"]))
    loop_graph["body"]["nodes"][1]["outputs"].append({"port": "result", "source": {"kind": "output", "node_id": "loop", "port": "result"}})
    symbols = copy.deepcopy(definitions[0])
    symbols["campaign_id"] = "symbol-statistics"
    symbols["body"]["nodes"][0]["tool"] = sequence.lock["tool"]
    for name, ports in (("inputs", sequence.descriptor["inputs"]), ("outputs", sequence.descriptor["outputs"])):
        port = ports[0]
        symbols["body"][name][0]["value_type"] = {"kind": "artifact", "media_type": "application/json", **{
            key: port[key] for key in ("schema_ref", "representation", "unit")}}
    definitions.append(symbols)
    releases, schemas = [], []
    for tool in e.tools:
        path = e.root / (tool.key + "-release.json")
        path.write_text(json.dumps(tool.image["descriptor"]), encoding="utf-8")
        releases.append({"descriptor": path.name, "lock": tool.lock})
        for kind, ports in (("input", tool.descriptor["inputs"]), ("output", tool.descriptor["outputs"])):
            schemas.append({"schema_ref": ports[0]["schema_ref"], "path": tool.module + "-" + kind + ".json"})
    entries = []
    for value in definitions:
        path = e.root / (value["campaign_id"] + ".json")
        path.write_text(json.dumps(value), encoding="utf-8")
        entries.append({"definition": path.name, "releases": releases, "schemas": schemas})
    return entries
