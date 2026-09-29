CREATE TABLE runtime.graph_aggregate_cuts (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(64) NOT NULL,
 observed_revision bigint NOT NULL CHECK (observed_revision BETWEEN 0 AND 9007199254740990),
 closure_revision bigint NOT NULL CHECK (closure_revision=observed_revision+1),
 audit_ordinal integer NOT NULL DEFAULT 0 CHECK (audit_ordinal=0),
 cut_sha256 varchar(64) NOT NULL CHECK (cut_sha256 ~ '^[0-9a-f]{64}$'),
 document jsonb NOT NULL CHECK (jsonb_typeof(document)='object'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,run_id,activation_id),
 FOREIGN KEY (tenant_id,project_id,run_id,activation_id) REFERENCES runtime.graph_nodes,
 FOREIGN KEY (tenant_id,project_id,run_id,closure_revision,audit_ordinal)
  REFERENCES runtime.audit_events(tenant_id,project_id,run_id,revision,ordinal)
  DEFERRABLE INITIALLY DEFERRED
);
GRANT SELECT,INSERT ON runtime.graph_aggregate_cuts TO runtime_service;
