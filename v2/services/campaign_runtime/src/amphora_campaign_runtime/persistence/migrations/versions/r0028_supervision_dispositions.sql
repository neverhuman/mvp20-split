CREATE TABLE runtime.supervision_request_dispositions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 decision_id varchar(128) NOT NULL, request_sha256 varchar(64) NOT NULL,
 disposition_sha256 char(64) NOT NULL CHECK(disposition_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16384),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,run_id,decision_id,request_sha256),
 FOREIGN KEY(tenant_id,project_id,run_id,decision_id,request_sha256)
  REFERENCES runtime.supervision_execution_reports(tenant_id,project_id,run_id,decision_id,request_sha256)
);
GRANT SELECT,INSERT ON runtime.supervision_request_dispositions TO runtime_service;
