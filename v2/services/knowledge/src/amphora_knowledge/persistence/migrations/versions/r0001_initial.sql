CREATE TABLE knowledge.graph_profiles (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 vocabulary_sha256 char(64) NOT NULL CHECK(vocabulary_sha256 ~ '^[0-9a-f]{64}$'),
 policy_sha256 char(64) NOT NULL CHECK(policy_sha256 ~ '^[0-9a-f]{64}$'),
 vocabulary_bytes bytea NOT NULL CHECK(octet_length(vocabulary_bytes) BETWEEN 1 AND 262144),
 policy_bytes bytea NOT NULL CHECK(octet_length(policy_bytes) BETWEEN 1 AND 4096),
 PRIMARY KEY(tenant_id,project_id,graph_id)
);
CREATE TABLE knowledge.proposals (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 change_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,graph_id,change_id),
 FOREIGN KEY(tenant_id,project_id,graph_id) REFERENCES knowledge.graph_profiles
);
CREATE TABLE knowledge.decisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 change_id varchar(128) NOT NULL,
 outcome varchar(16) NOT NULL CHECK(outcome IN ('accepted','rejected','conflict')),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,graph_id,change_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,change_id) REFERENCES knowledge.proposals
);
CREATE TABLE knowledge.accepted_changes (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 position bigint NOT NULL CHECK(position BETWEEN 1 AND 9007199254740991),
 prior_position bigint,
 change_id varchar(128) NOT NULL,
 change_sha256 char(64) NOT NULL CHECK(change_sha256 ~ '^[0-9a-f]{64}$'),
 snapshot_sha256 char(64) NOT NULL CHECK(snapshot_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 1048576),
 PRIMARY KEY(tenant_id,project_id,graph_id,position),
 UNIQUE(tenant_id,project_id,graph_id,change_id),
 UNIQUE(tenant_id,project_id,graph_id,position,change_id,change_sha256,snapshot_sha256),
 CHECK((position=1 AND prior_position IS NULL) OR
       (position>1 AND prior_position IS NOT NULL AND prior_position=position-1)),
 FOREIGN KEY(tenant_id,project_id,graph_id,change_id) REFERENCES knowledge.proposals,
 FOREIGN KEY(tenant_id,project_id,graph_id,prior_position) REFERENCES knowledge.accepted_changes
);
CREATE TABLE knowledge.snapshots (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 revision bigint NOT NULL,
 snapshot_sha256 char(64) NOT NULL,
 change_id varchar(128) NOT NULL, change_sha256 char(64) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16777216),
 PRIMARY KEY(tenant_id,project_id,graph_id,revision),
 UNIQUE(tenant_id,project_id,graph_id,revision,snapshot_sha256),
 FOREIGN KEY(tenant_id,project_id,graph_id,revision,change_id,change_sha256,snapshot_sha256)
 REFERENCES knowledge.accepted_changes(tenant_id,project_id,graph_id,position,change_id,change_sha256,snapshot_sha256)
);
ALTER TABLE knowledge.accepted_changes ADD CONSTRAINT accepted_snapshot_binding
 FOREIGN KEY(tenant_id,project_id,graph_id,position,snapshot_sha256)
 REFERENCES knowledge.snapshots(tenant_id,project_id,graph_id,revision,snapshot_sha256)
 DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE knowledge.heads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 revision bigint NOT NULL, snapshot_sha256 char(64) NOT NULL,
 change_id varchar(128) NOT NULL, change_sha256 char(64) NOT NULL,
 PRIMARY KEY(tenant_id,project_id,graph_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,revision,snapshot_sha256) REFERENCES knowledge.snapshots(tenant_id,project_id,graph_id,revision,snapshot_sha256),
 FOREIGN KEY(tenant_id,project_id,graph_id,revision,change_id,change_sha256,snapshot_sha256)
 REFERENCES knowledge.accepted_changes(tenant_id,project_id,graph_id,position,change_id,change_sha256,snapshot_sha256)
);
GRANT SELECT, INSERT ON knowledge.graph_profiles,knowledge.proposals,knowledge.decisions,knowledge.accepted_changes,knowledge.snapshots,knowledge.heads TO knowledge_service;
GRANT UPDATE(revision,snapshot_sha256,change_id,change_sha256) ON knowledge.heads TO knowledge_service;
