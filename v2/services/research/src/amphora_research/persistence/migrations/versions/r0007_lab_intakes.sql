CREATE TABLE research.lab_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 intake_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 2097152),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,intake_id)
);
CREATE TABLE research.lab_terminals (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 intake_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 8388608),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,intake_id),
 FOREIGN KEY(tenant_id,project_id,intake_id) REFERENCES research.lab_intents
);
CREATE TABLE research.lab_observations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 intake_id varchar(128) NOT NULL,
 observation_id varchar(128) NOT NULL, revision integer NOT NULL CHECK(revision > 0),
 PRIMARY KEY(tenant_id,project_id,intake_id,observation_id),
 FOREIGN KEY(tenant_id,project_id,intake_id) REFERENCES research.lab_terminals,
 FOREIGN KEY(tenant_id,project_id,observation_id,revision) REFERENCES research.observation_revisions
);
GRANT SELECT, INSERT ON research.lab_intents,research.lab_terminals,research.lab_observations TO research_service;
