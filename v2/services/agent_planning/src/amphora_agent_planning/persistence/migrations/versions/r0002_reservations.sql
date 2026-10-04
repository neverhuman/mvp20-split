CREATE TABLE planning.budget_policies (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 policy_sha256 char(64) NOT NULL CHECK(policy_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16384),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id),
 UNIQUE(tenant_id,project_id,engagement_id,policy_sha256),
 FOREIGN KEY(tenant_id,project_id,engagement_id,request_sha256)
 REFERENCES planning.requests(tenant_id,project_id,engagement_id,request_sha256)
);
CREATE TABLE planning.reservations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 ordinal integer NOT NULL,
 policy_sha256 char(64) NOT NULL CHECK(policy_sha256 ~ '^[0-9a-f]{64}$'),
 input_tokens bigint NOT NULL CHECK(input_tokens BETWEEN 1 AND 16777216),
 output_tokens bigint NOT NULL CHECK(output_tokens BETWEEN 1 AND 16777216),
 accounting_units bigint NOT NULL CHECK(accounting_units BETWEEN 1 AND 9007199254740991),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal) REFERENCES planning.attempts,
 FOREIGN KEY(tenant_id,project_id,engagement_id,policy_sha256)
 REFERENCES planning.budget_policies(tenant_id,project_id,engagement_id,policy_sha256)
);
GRANT SELECT,INSERT ON planning.budget_policies,planning.reservations TO planning_service;
