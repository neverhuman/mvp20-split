CREATE TABLE planning.dispatches (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 ordinal integer NOT NULL, token uuid NOT NULL,
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(), deadline timestamptz NOT NULL,
 CHECK(deadline > registered_at),
 PRIMARY KEY(tenant_id,project_id,engagement_id,ordinal), UNIQUE(token),
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal) REFERENCES planning.reservations
);
CREATE TABLE planning.late_observations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 ordinal integer NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 capture_bytes bytea NOT NULL CHECK(octet_length(capture_bytes) <= 65536),
 input_tokens bigint NOT NULL CHECK(input_tokens BETWEEN 1 AND 16777216),
 output_tokens bigint NOT NULL CHECK(output_tokens BETWEEN 1 AND 16777216),
 accounting_units bigint NOT NULL CHECK(accounting_units BETWEEN 1 AND 9007199254740991),
 overage boolean NOT NULL,
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal) REFERENCES planning.dispatches,
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal) REFERENCES planning.observations
);
GRANT SELECT,INSERT ON planning.dispatches,planning.late_observations TO planning_service;
