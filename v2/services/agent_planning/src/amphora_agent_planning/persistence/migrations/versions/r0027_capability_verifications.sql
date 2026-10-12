CREATE TABLE planning.capability_verifications (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 fulfillment_id varchar(128) NOT NULL, request_id varchar(128) NOT NULL,
 status varchar(16) NOT NULL CHECK(status IN ('verified','rejected')),
 receipt_bytes bytea NOT NULL CHECK(octet_length(receipt_bytes) BETWEEN 1 AND 262144),
 receipt_sha256 char(64) NOT NULL CHECK(receipt_sha256 ~ '^[0-9a-f]{64}$'),
 witness_bytes bytea CHECK(octet_length(witness_bytes) BETWEEN 1 AND 1048576),
 witness_sha256 char(64) CHECK(witness_sha256 ~ '^[0-9a-f]{64}$'),
 recorded_at timestamptz NOT NULL,
 CHECK((witness_bytes IS NULL) = (witness_sha256 IS NULL)),
 CHECK(status <> 'verified' OR witness_bytes IS NOT NULL),
 PRIMARY KEY(tenant_id,project_id,fulfillment_id),
 FOREIGN KEY(tenant_id,project_id,fulfillment_id)
 REFERENCES planning.capability_fulfillments(tenant_id,project_id,fulfillment_id)
);
CREATE UNIQUE INDEX capability_verification_winner ON planning.capability_verifications
 (tenant_id,project_id,request_id) WHERE status='verified';
GRANT SELECT,INSERT ON planning.capability_verifications TO planning_service;
