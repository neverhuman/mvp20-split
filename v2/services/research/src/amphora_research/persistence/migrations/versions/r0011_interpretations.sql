CREATE TABLE research.interpretation_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(32) NOT NULL CHECK(kind IN ('normalization','observation-use')), interpretation_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 2097152),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,kind,interpretation_id)
);
CREATE TABLE research.interpretation_results (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(32) NOT NULL, interpretation_id varchar(128) NOT NULL,
 sha256 char(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 8388608),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,kind,interpretation_id),
 FOREIGN KEY(tenant_id,project_id,kind,interpretation_id) REFERENCES research.interpretation_intents
);
CREATE TABLE research.interpretation_sources (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(32) NOT NULL, interpretation_id varchar(128) NOT NULL,
 artifact_id varchar(128) NOT NULL, reference_bytes bytea NOT NULL CHECK(octet_length(reference_bytes) BETWEEN 1 AND 16384),
 PRIMARY KEY(tenant_id,project_id,kind,interpretation_id,artifact_id),
 FOREIGN KEY(tenant_id,project_id,kind,interpretation_id) REFERENCES research.interpretation_results
);
CREATE INDEX interpretation_source_impact ON research.interpretation_sources(tenant_id,project_id,artifact_id,kind,interpretation_id);
CREATE TABLE research.interpretation_observations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(32) NOT NULL, interpretation_id varchar(128) NOT NULL,
 observation_id varchar(128) NOT NULL, observation_revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,kind,interpretation_id,observation_id,observation_revision),
 FOREIGN KEY(tenant_id,project_id,kind,interpretation_id) REFERENCES research.interpretation_results,
 FOREIGN KEY(tenant_id,project_id,observation_id,observation_revision) REFERENCES research.observation_revisions
);
CREATE INDEX interpretation_observation_impact ON research.interpretation_observations(tenant_id,project_id,observation_id,observation_revision,kind,interpretation_id);
CREATE TABLE research.interpretation_material_states (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(32) NOT NULL, interpretation_id varchar(128) NOT NULL,
 state_id varchar(128) NOT NULL, state_revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,kind,interpretation_id,state_id,state_revision),
 FOREIGN KEY(tenant_id,project_id,kind,interpretation_id) REFERENCES research.interpretation_results,
 FOREIGN KEY(tenant_id,project_id,state_id,state_revision) REFERENCES research.material_state_revisions
);
CREATE INDEX interpretation_state_impact ON research.interpretation_material_states(tenant_id,project_id,state_id,state_revision,kind,interpretation_id);
CREATE TABLE research.interpretation_experiments (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(32) NOT NULL, interpretation_id varchar(128) NOT NULL,
 experiment_id varchar(128) NOT NULL, experiment_revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,kind,interpretation_id),
 FOREIGN KEY(tenant_id,project_id,kind,interpretation_id) REFERENCES research.interpretation_results,
 FOREIGN KEY(tenant_id,project_id,experiment_id,experiment_revision) REFERENCES research.experiment_revisions
);
GRANT SELECT,INSERT ON research.interpretation_intents,research.interpretation_results,
 research.interpretation_sources,research.interpretation_observations,
 research.interpretation_material_states,research.interpretation_experiments TO research_service;
