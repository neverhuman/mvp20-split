CREATE TABLE runtime.supervision_winners (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 decision_id varchar(64) NOT NULL, kind varchar(32) NOT NULL
  CHECK (kind IN ('model_accepted','fallback','cancelled')),
 decision_sha256 varchar(64) NOT NULL CHECK (decision_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_decision bytea NOT NULL CHECK (octet_length(canonical_decision) BETWEEN 1 AND 262144),
 response_id varchar(128), selection_seed bytea, canonical_selection bytea,
 operation_id varchar(128) NOT NULL UNIQUE REFERENCES runtime.outbox(operation_id),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,run_id,decision_id),
 FOREIGN KEY (tenant_id,project_id,run_id,decision_id)
  REFERENCES runtime.supervision_checkpoints(tenant_id,project_id,run_id,decision_id),
 FOREIGN KEY (tenant_id,project_id,response_id)
  REFERENCES runtime.supervision_responses(tenant_id,project_id,response_id),
 CHECK ((kind='model_accepted') = (response_id IS NOT NULL)),
 CHECK ((selection_seed IS NULL) = (canonical_selection IS NULL)),
 CHECK (canonical_selection IS NULL OR (kind='model_accepted' AND
  octet_length(canonical_selection) BETWEEN 1 AND 262144 AND
  octet_length(selection_seed) BETWEEN 1 AND 16777216))
);
GRANT SELECT,INSERT ON runtime.supervision_winners TO runtime_service;
