CREATE TABLE planning.trace_publications (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, trace_id varchar(128) NOT NULL, trace_sha256 char(64) NOT NULL,
 publisher_id varchar(128) NOT NULL, schema_sha256 char(64) NOT NULL CHECK(schema_sha256 ~ '^[0-9a-f]{64}$'),
 identity_sha256 char(64) NOT NULL CHECK(identity_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16384),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,trace_id,trace_sha256)
 REFERENCES planning.extraction_traces(tenant_id,project_id,trace_id,trace_sha256)
);
CREATE TABLE planning.trace_publication_control (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 holder varchar(128), fence bigint NOT NULL DEFAULT 0 CHECK(fence BETWEEN 0 AND 9007199254740991),
 expires_at timestamptz, position integer NOT NULL DEFAULT 0 CHECK(position BETWEEN 0 AND 64),
 CHECK((holder IS NULL) = (expires_at IS NULL)),
 PRIMARY KEY(tenant_id,project_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.trace_publications
);
CREATE TABLE planning.trace_publication_payloads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 trace_bytes bytea NOT NULL CHECK(octet_length(trace_bytes) BETWEEN 1 AND 1048576),
 review_bytes bytea NOT NULL CHECK(octet_length(review_bytes) BETWEEN 1 AND 4194304),
 manifest_bytes bytea NOT NULL CHECK(octet_length(manifest_bytes) BETWEEN 1 AND 262144),
 payload_sha256 char(64) NOT NULL CHECK(payload_sha256 ~ '^[0-9a-f]{64}$'),
 prepared_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.trace_publications
);
CREATE TABLE planning.trace_publication_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 position integer NOT NULL CHECK(position BETWEEN 1 AND 64),
 event_sha256 char(64) NOT NULL CHECK(event_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id,position),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.trace_publication_payloads
);
GRANT SELECT,INSERT ON planning.trace_publications,planning.trace_publication_control,
 planning.trace_publication_payloads,planning.trace_publication_events TO planning_service;
GRANT UPDATE(holder,fence,expires_at,position) ON planning.trace_publication_control TO planning_service;
