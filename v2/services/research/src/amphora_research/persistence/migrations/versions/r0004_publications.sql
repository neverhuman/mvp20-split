CREATE TABLE research.publication_headers (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, assessment_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 2097152),
 PRIMARY KEY(tenant_id,project_id,assessment_id),
 FOREIGN KEY(tenant_id,project_id,assessment_id) REFERENCES research.assessment_decisions
);
CREATE TABLE research.publication_leases (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, assessment_id varchar(128) NOT NULL,
 holder uuid, fence bigint NOT NULL DEFAULT 0 CHECK(fence>=0), expires_at timestamptz,
 PRIMARY KEY(tenant_id,project_id,assessment_id),
 FOREIGN KEY(tenant_id,project_id,assessment_id) REFERENCES research.publication_headers
);
CREATE TABLE research.publication_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, assessment_id varchar(128) NOT NULL,
 position integer NOT NULL CHECK(position BETWEEN 1 AND 48),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 2097152),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,assessment_id,position),
 FOREIGN KEY(tenant_id,project_id,assessment_id) REFERENCES research.publication_headers
);
GRANT SELECT,INSERT ON research.publication_headers,research.publication_leases,research.publication_events TO research_service;
GRANT UPDATE(holder,fence,expires_at) ON research.publication_leases TO research_service;
