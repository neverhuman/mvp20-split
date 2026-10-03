CREATE TABLE research.scientific_input_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL CHECK(kind IN ('eligibility','synthesis')), decision_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 2097152),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,kind,decision_id)
);
CREATE TABLE research.scientific_input_outcomes (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL, decision_id varchar(128) NOT NULL,
 sha256 char(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,kind,decision_id),
 FOREIGN KEY(tenant_id,project_id,kind,decision_id) REFERENCES research.scientific_input_intents,
 FOREIGN KEY(tenant_id,project_id,kind,decision_id) REFERENCES research.scientific_decisions
);
GRANT SELECT,INSERT ON research.scientific_input_intents,research.scientific_input_outcomes TO research_service;
