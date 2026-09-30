CREATE TABLE research.identity_records (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL CHECK(kind IN ('candidate','sample','question','need')),
 identity_id varchar(128) NOT NULL,
 revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 prior_revision bigint,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,kind,identity_id,revision),
 CHECK((revision=1 AND prior_revision IS NULL) OR (revision>1 AND prior_revision=revision-1)),
 FOREIGN KEY(tenant_id,project_id,kind,identity_id,prior_revision)
 REFERENCES research.identity_records(tenant_id,project_id,kind,identity_id,revision)
);
CREATE TABLE research.identity_heads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL, identity_id varchar(128) NOT NULL,
 revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,kind,identity_id),
 FOREIGN KEY(tenant_id,project_id,kind,identity_id,revision)
 REFERENCES research.identity_records(tenant_id,project_id,kind,identity_id,revision)
);
CREATE TABLE research.identity_links (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL, identity_id varchar(128) NOT NULL, revision bigint NOT NULL,
 target_kind varchar(16) NOT NULL, target_id varchar(128) NOT NULL, target_revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,kind,identity_id,revision,target_kind,target_id,target_revision),
 FOREIGN KEY(tenant_id,project_id,kind,identity_id,revision) REFERENCES research.identity_records,
 FOREIGN KEY(tenant_id,project_id,target_kind,target_id,target_revision) REFERENCES research.identity_records
);
GRANT SELECT, INSERT ON research.identity_records,research.identity_heads,research.identity_links TO research_service;
GRANT UPDATE(revision) ON research.identity_heads TO research_service;
