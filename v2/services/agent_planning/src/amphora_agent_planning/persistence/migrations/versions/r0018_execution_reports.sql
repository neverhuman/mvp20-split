CREATE TABLE planning.checkpoint_execution_reports (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 report_sha256 char(64) NOT NULL CHECK(report_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 32768),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,engagement_id) REFERENCES planning.supervision_requests
);
GRANT SELECT,INSERT ON planning.checkpoint_execution_reports TO planning_service;
