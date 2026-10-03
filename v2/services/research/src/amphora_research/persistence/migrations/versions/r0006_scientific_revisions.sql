CREATE TABLE research.material_state_revisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 identity_id varchar(128) NOT NULL,
 revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 prior_revision bigint, actor_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 1048576),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,identity_id,revision),
 CHECK((revision=1 AND prior_revision IS NULL) OR
       (revision>1 AND prior_revision IS NOT NULL AND prior_revision=revision-1)),
 FOREIGN KEY(tenant_id,project_id,identity_id,prior_revision)
 REFERENCES research.material_state_revisions(tenant_id,project_id,identity_id,revision)
);
CREATE TABLE research.experiment_revisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 identity_id varchar(128) NOT NULL,
 revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 prior_revision bigint, actor_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 1048576),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,identity_id,revision),
 CHECK((revision=1 AND prior_revision IS NULL) OR
       (revision>1 AND prior_revision IS NOT NULL AND prior_revision=revision-1)),
 FOREIGN KEY(tenant_id,project_id,identity_id,prior_revision)
 REFERENCES research.experiment_revisions(tenant_id,project_id,identity_id,revision)
);
CREATE TABLE research.observation_revisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 identity_id varchar(128) NOT NULL,
 revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 prior_revision bigint, actor_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 1048576),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,identity_id,revision),
 CHECK((revision=1 AND prior_revision IS NULL) OR
       (revision>1 AND prior_revision IS NOT NULL AND prior_revision=revision-1)),
 FOREIGN KEY(tenant_id,project_id,identity_id,prior_revision)
 REFERENCES research.observation_revisions(tenant_id,project_id,identity_id,revision)
);
CREATE TABLE research.material_state_candidates (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 state_id varchar(128) NOT NULL, state_revision bigint NOT NULL,
 candidate_kind varchar(16) NOT NULL DEFAULT 'candidate' CHECK(candidate_kind='candidate'),
 candidate_id varchar(128) NOT NULL, candidate_revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,state_id,state_revision),
 FOREIGN KEY(tenant_id,project_id,state_id,state_revision) REFERENCES research.material_state_revisions,
 FOREIGN KEY(tenant_id,project_id,candidate_kind,candidate_id,candidate_revision) REFERENCES research.identity_records
);
CREATE TABLE research.sample_material_states (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 sample_kind varchar(16) NOT NULL DEFAULT 'sample' CHECK(sample_kind='sample'),
 sample_id varchar(128) NOT NULL, sample_revision bigint NOT NULL,
 state_id varchar(128) NOT NULL, state_revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,sample_id,sample_revision),
 FOREIGN KEY(tenant_id,project_id,sample_kind,sample_id,sample_revision) REFERENCES research.identity_records,
 FOREIGN KEY(tenant_id,project_id,state_id,state_revision) REFERENCES research.material_state_revisions
);
CREATE TABLE research.experiment_samples (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 experiment_id varchar(128) NOT NULL, experiment_revision bigint NOT NULL,
 sample_kind varchar(16) NOT NULL DEFAULT 'sample' CHECK(sample_kind='sample'),
 sample_id varchar(128) NOT NULL, sample_revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,experiment_id,experiment_revision,sample_id,sample_revision),
 FOREIGN KEY(tenant_id,project_id,experiment_id,experiment_revision) REFERENCES research.experiment_revisions,
 FOREIGN KEY(tenant_id,project_id,sample_kind,sample_id,sample_revision) REFERENCES research.identity_records
);
GRANT SELECT,INSERT ON research.material_state_revisions,research.experiment_revisions,
 research.observation_revisions,research.material_state_candidates,research.sample_material_states,
 research.experiment_samples TO research_service;
