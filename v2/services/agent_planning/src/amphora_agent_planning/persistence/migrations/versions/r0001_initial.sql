CREATE TABLE planning.requests (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id),
 UNIQUE(tenant_id,project_id,engagement_id,request_sha256)
);
CREATE TABLE planning.attempts (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL,
 ordinal integer NOT NULL CHECK(ordinal BETWEEN 1 AND 16),
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,engagement_id,request_sha256) REFERENCES planning.requests(tenant_id,project_id,engagement_id,request_sha256)
);
CREATE TABLE planning.observations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL, ordinal integer NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 capture_bytes bytea NOT NULL CHECK(octet_length(capture_bytes) BETWEEN 0 AND 65536),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal) REFERENCES planning.attempts
);
GRANT SELECT,INSERT ON planning.requests,planning.attempts,planning.observations TO planning_service;
