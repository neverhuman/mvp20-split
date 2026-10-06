CREATE TABLE runtime.supervision_policies (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 plan_sha256 varchar(64) NOT NULL,
 policy_sha256 varchar(64) NOT NULL CHECK (policy_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_policy bytea NOT NULL CHECK (octet_length(canonical_policy) BETWEEN 1 AND 262144),
 actor_id varchar(128) NOT NULL,
 family varchar(128) NOT NULL CHECK (family='graph.admit_supervised'),
 command_id varchar(128) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,run_id),
 UNIQUE (tenant_id,project_id,actor_id,family,command_id),
 FOREIGN KEY (tenant_id,project_id,run_id,plan_sha256)
  REFERENCES runtime.graph_runs(tenant_id,project_id,run_id,plan_sha256),
 FOREIGN KEY (tenant_id,project_id,actor_id,family,command_id)
  REFERENCES runtime.commands(tenant_id,project_id,actor_id,family,command_id)
);
GRANT SELECT,INSERT ON runtime.supervision_policies TO runtime_service;
