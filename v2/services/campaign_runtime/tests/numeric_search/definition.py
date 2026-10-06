"""Authored numeric search fixture; Runtime owns every scatter and repetition."""


from itertools import pairwise


def campaign(scope, releases, generations):
    if type(generations) is not int or not 0 <= generations <= 10000:
        raise ValueError("unsupported_generation_count")
    tools = {name: release["tool"] for name, release in releases.items()}
    limits = {"max_items": 128, "max_artifacts": 132, "max_bytes": 262144, "timeout_seconds": 120}

    def shape(stage, direction, name=None):
        value = next(port for port in tools[stage][direction] if name is None or port["name"] == name)
        return {"kind": "artifact", "media_type": "application/json",
                **{key: value[key] for key in ("schema_ref", "representation", "unit")}}

    def port(name, value_type):
        return {"name": name, "value_type": value_type}

    def source(name):
        return {"kind": "input", "name": name}

    def output(name, port="result"):
        return {"kind": "output", "node_id": name, "port": port}

    def finish(value, name="result"):
        return {"kind": "finish", "node_id": "finish", "outputs": [{"port": name, "source": value}]}

    def body(inputs, outputs, nodes):
        return {"inputs": inputs, "outputs": outputs, "nodes": nodes,
                "edges": [{"source": a["node_id"], "target": b["node_id"], "route": "next"}
                          for a, b in pairwise(nodes)]}

    def invoke(name, stage, value):
        return {"kind": "invoke", "node_id": name, "tool": tools[stage]["binding"],
                "inputs": [{"port": "parameters", "source": value}], "timeout_seconds": 60}

    def context(name, checkpoint, stage="requests", extra=()):
        return {"kind": "artifact_materialize", "node_id": name, "fields": [
            {"name": "original_specification", "mode": "inline", "source": source("specification")},
            {"name": "checkpoint", "mode": "inline", "source": checkpoint},
            {"name": "checkpoint_artifact", "mode": "references", "source": checkpoint}, *extra],
            "output": port("result", shape(stage, "inputs")), "limits": limits}

    requests = {"kind": "collection", "item": shape("evaluate", "inputs", "parameters"),
                "max_items": 128, "missing_slots": False}
    results = {"kind": "collection", "item": shape("evaluate", "outputs"),
               "max_items": 128, "missing_slots": True}
    state_shape = shape("seed", "outputs")
    policy_shape = shape("evaluate", "inputs", "policy")
    specification_shape = shape("seed", "inputs")

    def evaluate(checkpoint):
        evaluator = invoke("evaluate", "evaluate", source("candidate"))
        evaluator["inputs"].append({"port": "policy", "source": source("policy")})
        scatter = {"kind": "scatter", "node_id": "evaluate_batch", "collection": output("requests"),
            "item_input": "candidate", "captures": [{"port": "policy", "source": source("policy")}],
            "max_members": 128, "max_parallel": 8,
            "body": body([port("candidate", requests["item"]), port("policy", policy_shape)],
                [port("result", results["item"])], [evaluator, finish(output("evaluate"))]),
            "result_port": "result", "output": port("result", results),
            "policy": {"kind": "partial", "minimum": 0, "close": "all_terminal"}}
        return [context("request_context", checkpoint), invoke("expand", "requests", output("request_context")),
            {"kind": "artifact_project", "node_id": "requests", "source": output("expand"),
             "path": ["requests"], "mode": "items", "output": port("result", requests), "limits": limits},
            scatter, context("collection", checkpoint, "collect",
                             [{"name": "results", "mode": "inline", "source": output("evaluate_batch")}]),
            invoke("collect", "collect", output("collection"))]

    nodes = [invoke("seed", "seed", source("specification")), *evaluate(output("seed"))]
    final = output("collect")
    if generations:
        loop = body([port("state", state_shape), port("specification", specification_shape), port("policy", policy_shape)],
            [port("state", state_shape)], [context("variation_context", source("state"), "vary"),
            invoke("vary", "vary", output("variation_context")), *evaluate(output("vary")),
            finish(output("collect"), "state")])
        nodes.append({"kind": "iterate", "node_id": "generations", "state": [
            {"name": "state", "value_type": state_shape, "initial": final, "feedback_port": "state"}],
            "captures": [{"port": name, "source": source(name)} for name in ("specification", "policy")],
            "body": loop, "until": {"kind": "compare", "left": {"source": {"kind": "result", "name": "state"},
                "path": ["phase"], "value_type": {"kind": "scalar", "scalar": "string", "unit": "1"}},
                "operator": "eq", "right": {"kind": "string", "value": "stopped"}},
            "max_iterations": generations, "on_limit": "blocked"})
        final = output("generations", "state")
    nodes.append(finish(final))
    return {"schema_version": "4", "profile": "deterministic-v3", "scope": scope,
            "campaign_id": "numeric-search-fixture", "revision": 1, "context": [],
            "body": body([port("specification", specification_shape), port("policy", policy_shape)],
                         [port("result", state_shape)], nodes)}
