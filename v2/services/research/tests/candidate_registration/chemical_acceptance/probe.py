"""SDK-only controller: separate owner processes and real Artifact handoff."""

import hashlib
import copy
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
    drafts = module.load("chemical_draft_handoff", Path(__file__).with_name("draft_handoff.py"))
    e.public_http = http
    try:
        e.setup()
        for kind in module.KINDS:
            selection=e.registry_receipts[module.KINDS.index(kind)]["selection"]
            reference = e.publish_input(kind)
            port = e.descriptors[kind]["tool"]["inputs"][0]
            draft = drafts.prepare(e, kind)
            admission_command = e.command(
                    "graph.admit_draft",
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
                        "draft": draft,
                    },
                )
            admission = http.decoded(e.runtime.endpoint, "/v1/graph-runs/drafts", e.tokens["admin"], admission_command)
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
                "execution_profile": {"profile":"supplied-finite-structure-v1","scope":e.scope,
                    "release":module.GRAPH.BASE.WIRE.release_lock(e.descriptors[kind]),
                    "semantic_profile":e.semantic[kind]["profile"],"context":"supplied-finite-molecules"},
            }
            path = root / (kind + "-worker.json")
            path.write_text(json.dumps(worker), encoding="utf-8")
            process = subprocess.run(
                [
                    e.config[kind],
                    "-I",
                    "-m",
                    "amphora_chemical_structure",
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
            assert result["outcome"]["status"]=="derived"
            assert result["outcome"]["formula"]["text"]=="C4H10O3"
            assert result["source_sha256"]==hashlib.sha256((root/"supplied-request.json").read_bytes()).hexdigest()
            assert result["candidate"]=={"scope":e.scope,"candidate_id":"chemical","revision":1}
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
            wrong=copy.deepcopy(candidate)
            wrong["reference"]["candidate_id"]="foreign-candidate"
            status,_=http.request(e.research.endpoint,"/v1/candidates",e.tokens["admin"],wrong)
            assert status in (400,409,422), status
            assert http.request(e.research.endpoint,"/v1/candidates/read",e.tokens["admin"],wrong["reference"])[0]==404
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
        drafts.replace_without_grant(e, admission_command, admission, graph)
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
            "registry_receipts":e.registry_receipts,
            "wrong_candidate_rejected":True,
            "profile": "Independent Windows workers and actual Registry registration/activation plus Runtime/Data/Research APIs; declared fixture image pins, not built images or container deployment proof",
        }
        (root / "evidence.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )
        print("Chemical candidate handoff passed: " + str(root / "evidence.json"), flush=True)
    finally:
        e.close()


if __name__ == "__main__":
    main()
