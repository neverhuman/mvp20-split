CREATE TABLE planning.settlements (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 ordinal integer NOT NULL,
 observation_sha256 char(64) NOT NULL CHECK(observation_sha256 ~ '^[0-9a-f]{64}$'),
 charge_profile varchar(64) NOT NULL CHECK(charge_profile='reserved_floor_v1'),
 input_tokens bigint NOT NULL CHECK(input_tokens BETWEEN 1 AND 16777216),
 output_tokens bigint NOT NULL CHECK(output_tokens BETWEEN 1 AND 16777216),
 accounting_units bigint NOT NULL CHECK(accounting_units BETWEEN 1 AND 9007199254740991),
 overage boolean NOT NULL,
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal) REFERENCES planning.reservations,
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal) REFERENCES planning.observations
);
GRANT SELECT,INSERT ON planning.settlements TO planning_service;
