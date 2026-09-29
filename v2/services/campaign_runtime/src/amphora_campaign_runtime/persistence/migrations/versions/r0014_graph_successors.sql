CREATE TABLE runtime.graph_successors (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 parent_run_id varchar(128) NOT NULL, parent_plan_sha256 varchar(64) NOT NULL,
 parent_revision bigint NOT NULL CHECK (parent_revision BETWEEN 0 AND 9007199254740991),
 audit_ordinal integer NOT NULL DEFAULT 0 CHECK (audit_ordinal=0),
 admission_revision bigint NOT NULL DEFAULT 0 CHECK (admission_revision=0),
 carried jsonb NOT NULL CHECK (jsonb_typeof(carried)='array' AND jsonb_array_length(carried)<=64),
 transfer_sha256 varchar(64) NOT NULL CHECK (transfer_sha256 ~ '^[0-9a-f]{64}$'),
 PRIMARY KEY (tenant_id,project_id,run_id),
 CHECK (run_id<>parent_run_id),
 FOREIGN KEY (tenant_id,project_id,run_id) REFERENCES runtime.graph_runs,
 FOREIGN KEY (tenant_id,project_id,parent_run_id) REFERENCES runtime.graph_runs(tenant_id,project_id,run_id),
 FOREIGN KEY (tenant_id,project_id,parent_plan_sha256) REFERENCES runtime.graph_plans,
 FOREIGN KEY (tenant_id,project_id,parent_run_id,parent_revision,audit_ordinal)
  REFERENCES runtime.audit_events(tenant_id,project_id,run_id,revision,ordinal) DEFERRABLE INITIALLY DEFERRED,
 FOREIGN KEY (tenant_id,project_id,run_id,admission_revision,audit_ordinal)
  REFERENCES runtime.audit_events(tenant_id,project_id,run_id,revision,ordinal) DEFERRABLE INITIALLY DEFERRED
);
GRANT SELECT,INSERT ON runtime.graph_successors TO runtime_service;
