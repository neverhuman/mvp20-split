CREATE TABLE planning.capture_publications (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, publisher_id varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL, ordinal integer NOT NULL,
 observation_kind varchar(16) NOT NULL CHECK(observation_kind IN ('primary','late')),
 identity_sha256 char(64) NOT NULL CHECK(identity_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16384),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id),
 UNIQUE(tenant_id,project_id,engagement_id,ordinal,observation_kind),
 FOREIGN KEY(tenant_id,project_id,engagement_id) REFERENCES planning.supervision_requests,
 FOREIGN KEY(tenant_id,project_id,engagement_id) REFERENCES planning.campaign_preparations,
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal) REFERENCES planning.observations
);
CREATE TABLE planning.capture_publication_control (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 holder varchar(128), fence bigint NOT NULL DEFAULT 0 CHECK(fence BETWEEN 0 AND 9007199254740991),
 expires_at timestamptz, position integer NOT NULL DEFAULT 0 CHECK(position BETWEEN 0 AND 64),
 response_position integer NOT NULL DEFAULT 0 CHECK(response_position BETWEEN 0 AND 64),
 CHECK((holder IS NULL) = (expires_at IS NULL)),
 PRIMARY KEY(tenant_id,project_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.capture_publications
);
CREATE TABLE planning.capture_publication_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 position integer NOT NULL CHECK(position BETWEEN 1 AND 64),
 event_sha256 char(64) NOT NULL CHECK(event_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id,position),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.capture_publications
);
CREATE TABLE planning.capture_response_commands (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 command_sha256 char(64) NOT NULL CHECK(command_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.capture_publications
);
CREATE TABLE planning.capture_response_observations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, publication_id varchar(128) NOT NULL,
 position integer NOT NULL CHECK(position BETWEEN 1 AND 64),
 receipt_bytes bytea NOT NULL CHECK(octet_length(receipt_bytes) BETWEEN 1 AND 16384),
 readback_bytes bytea CHECK(octet_length(readback_bytes) BETWEEN 1 AND 262144),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,publication_id,position),
 FOREIGN KEY(tenant_id,project_id,publication_id) REFERENCES planning.capture_response_commands
);
GRANT SELECT,INSERT ON planning.capture_publications,planning.capture_publication_control,
 planning.capture_publication_events,planning.capture_response_commands,planning.capture_response_observations TO planning_service;
GRANT UPDATE(holder,fence,expires_at,position,response_position) ON planning.capture_publication_control TO planning_service;
