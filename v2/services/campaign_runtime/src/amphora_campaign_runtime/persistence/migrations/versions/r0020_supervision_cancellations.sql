CREATE TABLE runtime.supervision_cancellations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 decision_id varchar(128) NOT NULL, request_sha256 varchar(64) NOT NULL,
 cancellation_id varchar(128) NOT NULL, sequence integer NOT NULL CHECK (sequence BETWEEN 1 AND 16),
 cancellation_sha256 varchar(64) NOT NULL CHECK (cancellation_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_cancellation bytea NOT NULL CHECK (octet_length(canonical_cancellation) BETWEEN 1 AND 8192),
 actor_id varchar(128) NOT NULL, operation_id varchar(128) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,cancellation_id),
 UNIQUE (tenant_id,project_id,run_id,decision_id,request_sha256,sequence),
 UNIQUE (tenant_id,project_id,operation_id),
 FOREIGN KEY (tenant_id,project_id,run_id,decision_id,request_sha256)
  REFERENCES runtime.supervision_requests(tenant_id,project_id,run_id,decision_id,request_sha256),
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES runtime.commands(tenant_id,project_id,operation_id)
);
GRANT SELECT,INSERT ON runtime.supervision_cancellations TO runtime_service;
