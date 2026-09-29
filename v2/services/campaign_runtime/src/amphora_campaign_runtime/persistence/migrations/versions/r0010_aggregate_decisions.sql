ALTER TABLE runtime.graph_aggregate_cuts ADD CONSTRAINT graph_aggregate_exact_cut
 UNIQUE (tenant_id,project_id,run_id,activation_id,cut_sha256);
CREATE TABLE runtime.graph_aggregate_decisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(64) NOT NULL,
 cut_sha256 varchar(64) NOT NULL CHECK (cut_sha256 ~ '^[0-9a-f]{64}$'),
 decision_sha256 varchar(64) NOT NULL CHECK (decision_sha256 ~ '^[0-9a-f]{64}$'),
 document jsonb NOT NULL CHECK (jsonb_typeof(document)='object'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,run_id,activation_id),
 FOREIGN KEY (tenant_id,project_id,run_id,activation_id,cut_sha256)
  REFERENCES runtime.graph_aggregate_cuts(tenant_id,project_id,run_id,activation_id,cut_sha256)
);
GRANT SELECT,INSERT ON runtime.graph_aggregate_decisions TO runtime_service;
