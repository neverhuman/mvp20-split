CREATE TABLE research.assessment_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 assessment_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 2097152),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,assessment_id)
);
CREATE TABLE research.assessment_decisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 assessment_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 8388608),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,assessment_id),
 FOREIGN KEY(tenant_id,project_id,assessment_id) REFERENCES research.assessment_intents
);
GRANT SELECT, INSERT ON research.assessment_intents,research.assessment_decisions TO research_service;
