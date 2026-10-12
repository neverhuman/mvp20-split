CREATE TABLE planning.capability_fulfillments (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, command_id varchar(128) NOT NULL,
 fulfillment_id varchar(128) NOT NULL, request_id varchar(128) NOT NULL,
 command_sha256 char(64) NOT NULL CHECK(command_sha256 ~ '^[0-9a-f]{64}$'),
 command_bytes bytea NOT NULL CHECK(octet_length(command_bytes) BETWEEN 1 AND 262144),
 capability_sha256 char(64) NOT NULL CHECK(capability_sha256 ~ '^[0-9a-f]{64}$'),
 capability_bytes bytea NOT NULL CHECK(octet_length(capability_bytes) BETWEEN 1 AND 262144),
 receipt_sha256 char(64) NOT NULL CHECK(receipt_sha256 ~ '^[0-9a-f]{64}$'),
 receipt_bytes bytea NOT NULL CHECK(octet_length(receipt_bytes) BETWEEN 1 AND 262144),
 recorded_at timestamptz NOT NULL,
 PRIMARY KEY(tenant_id,project_id,actor_id,command_id),
 UNIQUE(tenant_id,project_id,fulfillment_id)
);
CREATE INDEX capability_fulfillment_request ON planning.capability_fulfillments
 (tenant_id,project_id,actor_id,request_id,recorded_at,fulfillment_id);
GRANT SELECT,INSERT ON planning.capability_fulfillments TO planning_service;
