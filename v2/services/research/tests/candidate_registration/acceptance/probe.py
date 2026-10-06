"""SDK-only controller: separate owner processes and real Artifact handoff."""

import importlib.util
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def main():
    assert all(
        importlib.util.find_spec(name) is None
        for name in (
            "sqlalchemy",
            "amphora_research",
            "amphora_campaign_runtime",
            "amphora_numeric_space",
        )
    )
    spec = importlib.util.spec_from_file_location(
        "candidate_handoff", Path(__file__).with_name("environment.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    config = json.loads(Path(sys.argv[1]).read_bytes())
    root = Path(config["evidence"])
    root.mkdir()
    e, http = module.CandidateEnvironment(config, root), module.HTTP
    reports = []
    try:
        e.setup()
        for kind in module.KINDS:
            reference = e.publish_input(kind)
            port = e.descriptors[kind]["tool"]["inputs"][0]
            admission = http.decoded(
                e.runtime.endpoint,
                "/v1/graph-runs",
                e.tokens["admin"],
                e.command(
                    "graph.admit",
                    {
                        "plan_sha256": e.plans["candidate-" + kind]["sha256"],
                        "inputs": [
                            {
                                "port": "parameters",
                                "value": {
                                    "kind": "artifact",
                                    "artifact": reference,
                                    "representation": port["representation"],
                                    "unit": "1",
                                },
                            }
                        ],
                        "budget": {"limit": 4},
                    },
                ),
            )
            assert admission["outcome"]["status"] == "accepted"
            e.active_run = admission["outcome"]["committed"]["object_id"]
            e.advance()
            worker = {
                "actor_id": "worker1",
                "scope": e.scope,
                "run_id": e.active_run,
                "image_sha256": "c" * 64,
                "runtime": {
                    "endpoint": e.runtime_relay.endpoint,
                    "token_env": "WORKER_TOKEN",
                },
                "artifacts": {
                    "endpoint": e.artifact.endpoint,
                    "token_env": "WORKER_TOKEN",
                },
                "lease_seconds": 90,
            }
            path = root / (kind + "-worker.json")
            path.write_text(json.dumps(worker), encoding="utf-8")
            process = subprocess.run(
                [
                    e.config[kind],
                    "-I",
                    "-m",
                    "amphora_" + kind + "_space",
                    "worker",
                    "--config",
                    str(path),
                ],
                cwd=root,
                env=dict(http.isolated_env(), WORKER_TOKEN=e.tokens["worker1"]),
                capture_output=True,
                check=False,
                timeout=120,
            )
            assert process.returncode == 0, process.stderr.decode()[-1000:]
            outcome = json.loads(process.stdout)
            assert (
                outcome["status"] == "completion_accepted"
                and outcome["outcome"] == "succeeded"
            ), outcome
            for _ in range(8):
                graph = e.advance()
                if graph["status"] == "completed":
                    break
            assert graph["status"] == "completed" and graph["spent"] == 1
            identity = next(
                event["identity"]
                for event in reversed(e.runtime_relay.events)
                if event.get("identity", {}).get("command_family") == "runtime.complete"
            )
            receipt = http.decoded(
                e.runtime.endpoint,
                "/v1/commands/runtime.complete/"
                + identity["command_id"]
                + "?actor_id=worker1",
                e.tokens["admin"],
            )
            completion = http.decoded(
                e.runtime.endpoint,
                "/v1/runs/"
                + e.active_run
                + "/completions/"
                + receipt["outcome"]["committed"]["object_id"],
                e.tokens["admin"],
            )
            assert completion["canonical_result"]
            artifact = completion["result"]["outcome"]["outputs"][0]["artifact"]
            result = http.decoded(
                e.artifact.endpoint,
                "/v1/artifacts/" + artifact["artifact_id"] + "/content",
                e.tokens["worker1"],
            )
            design = result["result"]
            if kind == "numeric":
                assert design["coordinates"][0]["value"] == -1
            elif kind == "sequence":
                assert design["sequence"] == "AGGT"
            else:
                assert [site["unit_id"] for site in design["sites"]] == ["A", "A"]
                assert all(value is None for value in design["metadata"].values())
            candidate = {
                "wire_version": "1",
                "reference": {"scope": e.scope, "candidate_id": kind, "revision": 1},
                "representation": artifact,
                "supersedes": None,
            }
            assert (
                http.decoded(
                    e.research.endpoint, "/v1/candidates", e.tokens["admin"], candidate
                )
                == candidate
            )
            assert (
                http.decoded(
                    e.research.endpoint, "/v1/candidates", e.tokens["admin"], candidate
                )
                == candidate
            )
            assert (
                http.decoded(
                    e.research.endpoint,
                    "/v1/candidates/read",
                    e.tokens["admin"],
                    candidate["reference"],
                )
                == candidate
            )
            e.owner_command("deliver", "--limit", "100", "--time-budget", "10")
            reservations = [
                http.decoded(
                    e.artifact.endpoint, "/v1/reservations/" + key, e.tokens["runtime"]
                )
                for key in completion["retention_reservation_ids"]
            ]
            assert reservations and all(
                item["outcome"]["status"] == "confirmed" for item in reservations
            )
            reports.append(
                {
                    "kind": kind,
                    "graph": graph,
                    "completion": completion,
                    "candidate": candidate,
                    "result": result,
                    "reservations": reservations,
                }
            )
        old = e.research
        old.close()
        e.research = http.Service(
            old.python, old.module, old.config, old.env, root, old.port
        )
        e.resources.append(e.research)
        e.research.ready(e.tokens["admin"], "/health")
        data_port = e.artifact.port
        e.artifact.close()
        e.artifact_config["principals"] = [
            item
            for item in e.artifact_config["principals"]
            if item["actor_id"] != "research"
        ]
        e.artifact = e.host(
            "artifact",
            "amphora_data_artifacts",
            e.artifact_config,
            "AMPHORA_ARTIFACT_DATABASE_URL",
            data_port,
        )
        for report in reports:
            candidate = report["candidate"]
            assert (
                http.request(
                    e.research.endpoint, "/v1/candidates", e.tokens["admin"], candidate
                )[0]
                == 403
            )
            assert (
                http.decoded(
                    e.research.endpoint,
                    "/v1/candidates/read",
                    e.tokens["admin"],
                    candidate["reference"],
                )
                == candidate
            )
        evidence = {
            "status": "passed",
            "timestamp_local": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            "scope": e.scope,
            "packages": config["packages"],
            "reports": reports,
            "rights_denial_preserves_history": True,
            "research_restart_preserves_history": True,
            "profile": "Independent Windows workers and actual Runtime/Data/Research APIs; declared image pins, not built images or Registry/deployment proof",
        }
        (root / "evidence.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )
        print("Candidate handoff passed: " + str(root / "evidence.json"), flush=True)
    finally:
        e.close()


if __name__ == "__main__":
    main()
