"""Test-only public HTTP bridge; Runtime compilation/migration stay in its interpreter."""
import copy
import importlib.util
import json
import os
import socket
import subprocess
import uuid
from pathlib import Path


class DomainRuntime:
    def __init__(self, root, scope, environment, python, owner_factory):
        self.root, self.scope, self.environment = root, scope, environment
        self.python, self.owner_factory = python, owner_factory
        self.runtime = None
        self.faults = None
        self.results = {}
        with socket.socket() as listener:
            listener.bind(("127.0.0.1",0))
            self.port = listener.getsockname()[1]
        self.endpoint = "http://127.0.0.1:" + str(self.port)
        self.environment.update(RUNTIME_ADMIN_TOKEN="u"*32,RUNTIME_ISSUER_TOKEN="j"*32,
                                RUNTIME_OUTCOME_TOKEN="o"*32,RUNTIME_RETENTION_TOKEN="t"*32,
                                RUNTIME_CURSOR_KEY="c"*32)
        self.path = root / "domain-runtime.json"

    def data_configuration(self, config):
        config["runtime"] = {"owner":"runtime", "endpoint":self.endpoint + "/v1/completion-intents/outcome",
                             "token_env":"RUNTIME_OUTCOME_TOKEN"}
        config["principals"].append({"token_env":"RUNTIME_RETENTION_TOKEN", "actor_id":"runtime",
                                    "scope":self.scope,"actions":["retention","read"]})
        return config

    def attach_data(self, endpoint):
        self.data = endpoint
        if os.environ.get("AMPHORA_TEST_DOMAIN_FAULTS") == "1":
            spec = importlib.util.spec_from_file_location("domain_faults", Path(__file__).with_name("domain_faults.py"))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.faults = module.DomainFaults(self, endpoint)
            self.data = self.faults.relay.endpoint

    def command(self, family, payload, actor="admin"):
        return {"identity":{"scope":self.scope,"actor_id":actor,"command_family":family,
                            "command_id":uuid.uuid4().hex},"payload":payload}

    def _start(self):
        if self.runtime is not None:
            self.runtime.stop()
        self.runtime = self.owner_factory("amphora_campaign_runtime",self.path,self.environment,"u"*32,
                                          self.python,port=self.port)

    def stop(self):
        if self.runtime is not None:
            try:
                if hasattr(self, "run") and self.runtime.process.poll() is None:
                    page = self.runtime.request("/v2/graph-runs/" + self.run)
                    if page["status"] == "running":
                        reply = self.runtime.request("/v1/runs/cancel", self.command("runtime.cancel",
                            {"run_id":self.run,"reason_code":"test_failure_cleanup"}))
                        assert reply["outcome"]["status"] == "accepted", reply
            finally:
                self.runtime.stop()
                if self.faults is not None:
                    self.faults.close()

    def open_graph(self, family, view, configure=None):
        receipt = view["record"]["receipt"]
        subject, output = receipt["subject"], receipt["outcome"]["output"]
        # The fixture retains exact source/output schema bytes beside peer configuration.
        raw_document = b'{"type":"string","contentEncoding":"base64"}'
        (self.root / "context-schema.json").write_bytes(raw_document)
        output_schema = "assessment.json" if family.startswith("assessment") else "reasoning.json"
        input_type = {"kind":"artifact","schema_ref":subject["schema_ref"],"representation":"domain-context",
                      "unit":"1","media_type":subject["media_type"]}
        output_type = {"kind":"artifact","schema_ref":output["artifact"]["schema_ref"],
                       "representation":output["representation"],"unit":output["unit"],
                       "media_type":output["artifact"]["media_type"]}
        definition = {"schema_version":"3","profile":"deterministic-v2","campaign_id":family + "-receipt-run",
            "revision":1,"scope":self.scope,"context":[],"body":{
                "inputs":[{"name":"subject","value_type":input_type}],
                "outputs":[{"name":"result","value_type":output_type}],
                "nodes":[{"kind":"await","node_id":"evidence","issuer_id":receipt["issuer_id"],
                    "purpose":receipt["purpose"],"expected_revision":receipt["revision"],
                    "subject":{"kind":"input","name":"subject"},"output":{"name":"result","value_type":output_type},
                    "timeout_seconds":120,"on_timeout":"abstained"},
                    {"kind":"finish","node_id":"finish","outputs":[{"port":"result",
                      "source":{"kind":"output","node_id":"evidence","port":"result"}}]}],
                "edges":[{"source":"evidence","target":"finish","route":"next"}]}}
        inputs = [{"port":"subject","value":{"kind":"artifact","artifact":subject,
                   "representation":"domain-context","unit":"1"}}]
        if configure is not None:
            configure(definition, inputs)
        definition_path = self.root/(family + "-runtime-graph.json")
        definition_path.write_text(json.dumps(definition),encoding="utf-8")
        config = {"database_url_env":"RUNTIME_DB","inspection":{"cursor_key_env":"RUNTIME_CURSOR_KEY"},"fixtures":[],"principals":[
            {"token_env":"RUNTIME_ADMIN_TOKEN","actor_id":"admin","scope":self.scope,"actions":["admit","maintain","read","deliver","cancel"]},
            {"token_env":"RUNTIME_ISSUER_TOKEN","actor_id":receipt["issuer_id"],"scope":self.scope,"actions":["submit_receipt","read"]},
            {"token_env":"RUNTIME_OUTCOME_TOKEN","actor_id":"artifact-service","scope":self.scope,"actions":["outcome"]}],
            "artifacts":{"runtime_owner":"runtime","reserve_endpoint":self.data + "/v1/reservations","token_env":"RUNTIME_RETENTION_TOKEN"},
            "graphs":[{"definition":definition_path.name,"releases":[],"schemas":[
                {"schema_ref":subject["schema_ref"],"path":"context-schema.json"},
                {"schema_ref":output["artifact"]["schema_ref"],"path":output_schema}]}]}
        self.path.write_text(json.dumps(config),encoding="utf-8")
        clean = {key:value for key,value in os.environ.items() if key.upper() in
                 {"SYSTEMROOT","WINDIR","PATH","TEMP","TMP","USERPROFILE","LOCALAPPDATA","APPDATA","COMSPEC"}}
        compiled = subprocess.run([self.python,"-I",str(Path(__file__).with_name("compile_plan.py")),str(self.path)],
                                  env=clean,capture_output=True,text=True,encoding="utf-8",timeout=30)
        assert compiled.returncode == 0, compiled.stderr[-2000:]
        plan = json.loads(compiled.stdout)[definition["campaign_id"]]
        self._start()
        admission = self.command("graph.admit",{"plan_sha256":plan["sha256"],"inputs":inputs,"budget":{"limit":1}})
        admitted = self.runtime.request("/v1/graph-runs",admission)
        assert admitted["outcome"]["status"] == "accepted", admitted
        self.run = admitted["outcome"]["committed"]["object_id"]
        self.runtime.request("/v1/graph-runs/advance",self.command("graph.advance",{"run_id":self.run}))
        page = self.runtime.request("/v2/graph-runs/" + self.run)
        return admitted, page

    def before(self, family, view):
        admitted, page = self.open_graph(family, view)
        receipt = view["record"]["receipt"]
        activation = next(node["activation_id"] for node in page["nodes"] if node["kind"] == "await")
        self.wait_path = "/v1/graph-runs/" + self.run + "/waits/" + activation
        self.opened = self.runtime.request(self.wait_path)
        assert self.opened["closure"] is None
        assert self.opened["expectation"]["expected_revision"] == receipt["revision"]
        self.results[family] = {"opened_before_correction":self.opened,"admission":admitted}

    def after(self, family, root, corrected):
        from amphora_tool_protocol import HttpTransport

        def submit(receipt, command=None, recover=False):
            expected = self.opened["expectation"]
            command = command or self.command("graph.submit_receipt",{"run_id":self.run,
                "activation_id":expected["activation_id"],"wait_revision":expected["wait_revision"],
                "expectation_sha256":self.opened["expectation_sha256"],"receipt":receipt},actor=receipt["issuer_id"])
            if recover and self.faults is not None:
                return command,self.faults.accept(command)
            response = HttpTransport(self.endpoint,"j"*32).request("POST","/v1/graph-receipts",json.dumps(command).encode())
            assert response.status == 200
            return command,json.loads(response.body)

        _, rejected = submit(corrected["record"]["notice"])
        assert rejected["outcome"]["reason_code"] == "wait_receipt_superseded"
        assert self.runtime.request(self.wait_path) == self.opened
        boundary_rejections = {}
        for field, reason in (("purpose","wait_receipt_purpose_mismatch"), ("subject","wait_receipt_subject_mismatch")):
            wrong = copy.deepcopy(root["record"]["receipt"])
            wrong["receipt_id"] = "boundary-" + uuid.uuid4().hex
            if field == "purpose":
                wrong[field] = "unrelated-purpose"
            else:
                wrong[field]["artifact_id"] = "unrelated-context"
            _, rejection = submit(wrong)
            assert rejection["outcome"]["reason_code"] == reason, rejection
            assert self.runtime.request(self.wait_path) == self.opened
            boundary_rejections[field] = rejection
        expected = self.opened["expectation"]
        unauthorized = self.command("graph.submit_receipt", {"run_id":self.run,
            "activation_id":expected["activation_id"],"wait_revision":expected["wait_revision"],
            "expectation_sha256":self.opened["expectation_sha256"],"receipt":root["record"]["receipt"]},
            actor=root["record"]["receipt"]["issuer_id"])
        denied = HttpTransport(self.endpoint,"u"*32).request("POST","/v1/graph-receipts",json.dumps(unauthorized).encode())
        assert denied.status == 403, (denied.status, denied.body)
        assert self.runtime.request(self.wait_path) == self.opened
        command, accepted = submit(root["record"]["receipt"],recover=True)
        assert accepted["outcome"]["status"] == "accepted", accepted
        closed = self.runtime.request(self.wait_path)
        assert closed["closure"]["outcome"]["receipt"] == root["record"]["receipt"]
        self.runtime.request("/v1/graph-runs/advance",self.command("graph.advance",{"run_id":self.run}))
        graph = self.runtime.request("/v2/graph-runs/" + self.run)
        assert graph["status"] == "completed" and graph["spent"] == graph["reserved"] == 0
        delivery = self.deliver() if self.faults is None else self.faults.confirm(root["record"]["receipt"]["outcome"]["output"])
        assert delivery["acknowledged"] == 1, delivery
        self._start()
        assert self.runtime.request(self.wait_path) == closed
        assert submit(root["record"]["receipt"],command)[1] == accepted
        self.results[family].update(boundary_rejections=boundary_rejections,unauthorized_status=denied.status,notice_rejected=rejected,accepted=accepted,closure=closed,graph=graph,delivery=delivery,
                                    replay_after_replacement=True,
                                    recovery=None if self.faults is None else copy.deepcopy(self.faults.evidence))

    def partial(self, proof):
        spec = importlib.util.spec_from_file_location("domain_partial", Path(__file__).with_name("domain_partial.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.prove_partial(self, proof.research["root"], proof.research["corrected"])

    def deliver(self, limit=100):
        delivered = subprocess.run([self.python,"-I","-m","amphora_campaign_runtime","deliver","--config",str(self.path),
            "--actor","admin","--tenant",self.scope["tenant_id"],"--project",self.scope["project_id"],
            "--limit",str(limit),"--time-budget","5"],env=self.environment,capture_output=True,text=True,encoding="utf-8",timeout=30)
        assert delivered.returncode == 0, "Runtime delivery failed"
        delivery = json.loads(delivered.stdout)
        return delivery
