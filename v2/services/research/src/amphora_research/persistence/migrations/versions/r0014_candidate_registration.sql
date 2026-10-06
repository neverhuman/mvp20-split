CREATE TABLE research.candidate_registrations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL CHECK(kind = 'candidate'),
 identity_id varchar(128) NOT NULL, revision bigint NOT NULL,
 actor_id varchar(128) NOT NULL CHECK(length(actor_id) BETWEEN 1 AND 128),
 record_sha256 varchar(64) NOT NULL CHECK(record_sha256 ~ '^[0-9a-f]{64}$'),
 preexisting boolean NOT NULL,
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,kind,identity_id,revision),
 FOREIGN KEY(tenant_id,project_id,kind,identity_id,revision)
 REFERENCES research.identity_records(tenant_id,project_id,kind,identity_id,revision)
);
GRANT SELECT, INSERT ON research.candidate_registrations TO research_service;
