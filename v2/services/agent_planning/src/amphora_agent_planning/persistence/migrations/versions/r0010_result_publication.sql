CREATE TABLE planning.result_publications (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, trace_id varchar(128) NOT NULL, trace_sha256 char(64) NOT NULL,
 interpretation_id varchar(128) NOT NULL, publisher_id varchar(128) NOT NULL,
 selection_sha256 char(64) NOT NULL CHECK(selection_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16384),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,trace_id,trace_sha256)
 REFERENCES planning.extraction_traces(tenant_id,project_id,trace_id,trace_sha256),
 FOREIGN KEY(tenant_id,project_id,interpretation_id)
 REFERENCES planning.trace_publications(tenant_id,project_id,publication_id)
);
CREATE TABLE planning.result_publication_control (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 holder varchar(128), fence bigint NOT NULL DEFAULT 0 CHECK(fence BETWEEN 0 AND 9007199254740991),
 expires_at timestamptz, position integer NOT NULL DEFAULT 0 CHECK(position BETWEEN 0 AND 64),
 CHECK((holder IS NULL) = (expires_at IS NULL)),
 PRIMARY KEY(tenant_id,project_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.result_publications
);
CREATE TABLE planning.result_publication_payloads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 body_bytes bytea NOT NULL CHECK(octet_length(body_bytes) BETWEEN 1 AND 262144),
 review_bytes bytea NOT NULL CHECK(octet_length(review_bytes) BETWEEN 1 AND 4194304),
 question_bytes bytea NOT NULL CHECK(octet_length(question_bytes) BETWEEN 1 AND 8388608),
 manifest_bytes bytea NOT NULL CHECK(octet_length(manifest_bytes) BETWEEN 1 AND 262144),
 payload_sha256 char(64) NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 prepared_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.result_publications
);
CREATE TABLE planning.result_publication_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 position integer NOT NULL CHECK(position BETWEEN 1 AND 64),
 event_sha256 char(64) NOT NULL CHECK(event_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id,position),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.result_publication_payloads
);
GRANT SELECT,INSERT ON planning.result_publications,planning.result_publication_control,
 planning.result_publication_payloads,planning.result_publication_events TO planning_service;
GRANT UPDATE(holder,fence,expires_at,position) ON planning.result_publication_control TO planning_service;
