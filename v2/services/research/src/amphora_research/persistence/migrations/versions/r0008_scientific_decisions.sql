-- Match the existing observation revision's bigint domain; do not rewrite applied0007.
ALTER TABLE research.lab_observations ALTER COLUMN revision TYPE bigint;
CREATE TABLE research.scientific_decisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL CHECK(kind IN ('eligibility','synthesis')), decision_id varchar(128) NOT NULL,
 sha256 char(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 8388608),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,kind,decision_id)
);
CREATE TABLE research.decision_sources (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL, decision_id varchar(128) NOT NULL,
 artifact_id varchar(128) NOT NULL, reference_bytes bytea NOT NULL,
 PRIMARY KEY(tenant_id,project_id,kind,decision_id,artifact_id),
 FOREIGN KEY(tenant_id,project_id,kind,decision_id) REFERENCES research.scientific_decisions
);
CREATE INDEX decision_sources_impact ON research.decision_sources(tenant_id,project_id,artifact_id,kind,decision_id);
CREATE TABLE research.decision_observations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL CHECK(kind='eligibility'), decision_id varchar(128) NOT NULL,
 observation_id varchar(128) NOT NULL, revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,kind,decision_id,observation_id,revision),
 FOREIGN KEY(tenant_id,project_id,kind,decision_id) REFERENCES research.scientific_decisions,
 FOREIGN KEY(tenant_id,project_id,observation_id,revision) REFERENCES research.observation_revisions
);
CREATE INDEX decision_observations_impact ON research.decision_observations(tenant_id,project_id,observation_id,revision,kind,decision_id);
CREATE TABLE research.decision_consumers (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL, decision_id varchar(128) NOT NULL,
 artifact_id varchar(128) NOT NULL, reference_bytes bytea NOT NULL,
 actor_id varchar(128) NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,kind,decision_id,artifact_id),
 FOREIGN KEY(tenant_id,project_id,kind,decision_id) REFERENCES research.scientific_decisions
);
GRANT SELECT, INSERT ON research.scientific_decisions,research.decision_sources,
 research.decision_observations,research.decision_consumers TO research_service;
