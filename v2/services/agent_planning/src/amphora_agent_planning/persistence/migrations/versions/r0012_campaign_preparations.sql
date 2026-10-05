CREATE TABLE planning.campaign_preparations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 manifest_sha256 char(64) NOT NULL CHECK(manifest_sha256 ~ '^[0-9a-f]{64}$'),
 plan_sha256 char(64) NOT NULL CHECK(plan_sha256 ~ '^[0-9a-f]{64}$'),
 packet_sha256 char(64) NOT NULL CHECK(packet_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 2097152),
 packet_bytes bytea NOT NULL CHECK(octet_length(packet_bytes) BETWEEN 1 AND 8388608),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,engagement_id,request_sha256)
 REFERENCES planning.requests(tenant_id,project_id,engagement_id,request_sha256)
);
GRANT SELECT,INSERT ON planning.campaign_preparations TO planning_service;
