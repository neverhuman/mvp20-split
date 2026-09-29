"""Authored dynamic round trip; arithmetic expectations live outside the graph builder."""

import copy


def dynamic_graph(template):
    raw = copy.deepcopy(template)
    raw.update(schema_version="4", profile="deterministic-v3", campaign_id="binding-round-trip")
    input_shape = raw["body"]["inputs"][0]["value_type"]
    output_shape = raw["body"]["outputs"][0]["value_type"]
    invoke_template = copy.deepcopy(raw["body"]["nodes"][0])
    scalar = {"kind": "scalar", "scalar": "number", "unit": "1"}
    collection = {"kind": "collection", "item": scalar, "max_items": 1024, "missing_slots": False}
    limits = {"max_items": 1024, "max_artifacts": 4, "max_bytes": 262144, "timeout_seconds": 120}

    def out(node, port="result"):
        return {"kind": "output", "node_id": node, "port": port}

    def port(name, shape):
        return {"name": name, "value_type": shape}

    def finish(source, name="result"):
        return {"kind": "finish", "node_id": "finish", "outputs": [{"port": name, "source": source}]}

    def body(inputs, outputs, nodes):
        return {"inputs": inputs, "outputs": outputs, "nodes": nodes,
                "edges": [{"source": a["node_id"], "target": b["node_id"], "route": "next"}
                          for a, b in zip(nodes, nodes[1:], strict=False)]}

    def invoke(name, source):
        return {**invoke_template, "node_id": name, "inputs": [{"port": "parameters", "source": source}]}

    def project(name, source, single=False):
        return {"kind": "artifact_project", "node_id": name, "source": source, "path": ["values", 0] if single else ["values"],
                "mode": "values", "output": port("result", scalar if single else collection), "limits": limits}

    def materialize(name, source, scale=1, offset=0):
        return {"kind": "artifact_materialize", "node_id": name, "fields": [
            {"name": "values", "mode": "inline", "source": source},
            {"name": "a", "mode": "inline", "source": {"kind": "integer", "value": scale, "unit": "1"}},
            {"name": "b", "mode": "inline", "source": {"kind": "integer", "value": offset, "unit": "1"}}],
            "output": port("result", input_shape), "limits": limits}

    singleton = {"kind": "join", "node_id": "singleton", "members": [{"member_id": "item", "source": {"kind": "input", "name": "item"}}],
                 "policy": {"kind": "all"}, "output": port("result", {**collection, "max_items": 1})}
    scoring = body([port("item", scalar)], [port("result", scalar)], [singleton,
        materialize("pack", out("singleton"), 2, 1), invoke("score", out("pack")),
        project("unpack", out("score"), True), finish(out("unpack"))])
    scatter = {"kind": "scatter", "node_id": "score_population", "collection": out("population"), "item_input": "item",
        "captures": [], "max_members": 1024, "max_parallel": 3, "body": scoring, "result_port": "result",
        "output": port("result", collection), "policy": {"kind": "all"}}
    iteration = body([port("parameters", input_shape)], [port("parameters", input_shape)], [
        invoke("producer", {"kind": "input", "name": "parameters"}), project("population", out("producer")), scatter,
        materialize("gather", out("score_population")), invoke("consumer", out("gather")),
        project("consumed", out("consumer")), materialize("feedback", out("consumed")), finish(out("feedback"), "parameters")])
    loop = {"kind": "iterate", "node_id": "generations", "state": [{"name": "parameters", "value_type": input_shape,
        "initial": {"kind": "input", "name": "parameters"}, "feedback_port": "parameters"}], "captures": [], "body": iteration,
        "until": {"kind": "constant", "value": False}, "max_iterations": 2, "on_limit": "finish"}
    raw["body"] = body([port("parameters", input_shape)], [port("result", input_shape)], [loop, finish(out("generations", "parameters"))])
    assert output_shape["kind"] == "artifact"
    return raw
