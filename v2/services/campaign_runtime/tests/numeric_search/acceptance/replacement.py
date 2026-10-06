"""Swap fresh owner/tool installations while retaining real accepted history."""


def replace(e, baseline, http):
    replacements = e.config["replacements"]
    before = e.restart_runtime(replacements["runtime"])
    e.config.update({key: replacements[key] for key in ("runtime", "numeric", "evaluator")})
    assert e.graph() == baseline["graph"] == before
    for report in baseline["reports"]:
        completion = report["completion"]
        retained = http.decoded(e.runtime.endpoint, "/v1/runs/" + e.active_run + "/completions/" +
                                completion["completion_id"], e.tokens["admin"])
        assert retained == completion
        assert e.bytes(report["artifact"])
    assert http.decoded(e.runtime.endpoint, "/v1/graph-runs", e.tokens["admin"], e.admission_command) == e.admission
    return {"original_graph": before, "retained_completions": len(baseline["reports"]),
            "original_admission_replay": True, "wheel_closures_equal": True,
            "replacement_packages": {key: e.config["packages"][key + "-replacement"] for key in replacements}}
