ALTER TABLE runtime.supervision_policies
 ADD UNIQUE (tenant_id,project_id,run_id,policy_sha256);
CREATE TABLE runtime.supervision_checkpoints (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(64) NOT NULL, decision_id varchar(64) NOT NULL,
 policy_sha256 varchar(64) NOT NULL, checkpoint_id varchar(128) NOT NULL,
 ordinal integer NOT NULL CHECK (ordinal BETWEEN 1 AND 100000),
 seed_sha256 varchar(64) NOT NULL CHECK (seed_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_seed bytea NOT NULL CHECK (octet_length(canonical_seed) BETWEEN 1 AND 16777216),
 eligibility varchar(32) NOT NULL CHECK (eligibility IN ('requestable','fallback_required')),
 reason_code varchar(128),
 created_at timestamptz NOT NULL, deadline timestamptz NOT NULL,
 PRIMARY KEY (tenant_id,project_id,run_id,activation_id),
 UNIQUE (tenant_id,project_id,run_id,decision_id),
 UNIQUE (tenant_id,project_id,run_id,ordinal),
 FOREIGN KEY (tenant_id,project_id,run_id,policy_sha256)
  REFERENCES runtime.supervision_policies(tenant_id,project_id,run_id,policy_sha256),
 FOREIGN KEY (tenant_id,project_id,run_id,activation_id)
  REFERENCES runtime.graph_nodes(tenant_id,project_id,run_id,activation_id),
 CHECK ((eligibility='requestable' AND reason_code IS NULL AND deadline>created_at) OR
  (eligibility='fallback_required' AND reason_code IS NOT NULL AND reason_code IN ('checkpoint_limit_exhausted','checkpoint_deadline_exhausted')))
);
GRANT SELECT,INSERT ON runtime.supervision_checkpoints TO runtime_service;
