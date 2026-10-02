CREATE TABLE knowledge.rebuild_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 rebuild_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 request_bytes bytea NOT NULL CHECK(octet_length(request_bytes) BETWEEN 1 AND 16384),
 initial_head bytea NOT NULL CHECK(octet_length(initial_head) BETWEEN 1 AND 16384),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,graph_id,rebuild_id),
 FOREIGN KEY(tenant_id,project_id,graph_id) REFERENCES knowledge.graph_profiles
);
CREATE TABLE knowledge.rebuild_candidates (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 candidate_id char(32) NOT NULL CHECK(candidate_id ~ '^[0-9a-f]{32}$'),
 rebuild_id varchar(128) NOT NULL, attempt integer NOT NULL CHECK(attempt BETWEEN 1 AND 3),
 revision bigint NOT NULL, snapshot_sha256 char(64) NOT NULL,
 change_id varchar(128) NOT NULL, change_sha256 char(64) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16777216),
 PRIMARY KEY(tenant_id,project_id,graph_id,candidate_id),
 UNIQUE(tenant_id,project_id,graph_id,rebuild_id,candidate_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,rebuild_id) REFERENCES knowledge.rebuild_intents,
 FOREIGN KEY(tenant_id,project_id,graph_id,revision,change_id,change_sha256,snapshot_sha256)
 REFERENCES knowledge.accepted_changes(tenant_id,project_id,graph_id,position,change_id,change_sha256,snapshot_sha256)
);
CREATE TABLE knowledge.rebuild_results (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 rebuild_id varchar(128) NOT NULL, outcome varchar(16) NOT NULL CHECK(outcome IN ('published','deferred','failed')),
 candidate_id char(32), attempts integer NOT NULL CHECK(attempts BETWEEN 1 AND 3), code varchar(128),
 decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,graph_id,rebuild_id),
 UNIQUE(tenant_id,project_id,graph_id,rebuild_id,candidate_id),
 CHECK((outcome='published' AND candidate_id IS NOT NULL AND code IS NULL)
    OR (outcome IN ('deferred','failed') AND candidate_id IS NULL AND code IS NOT NULL)),
 FOREIGN KEY(tenant_id,project_id,graph_id,rebuild_id) REFERENCES knowledge.rebuild_intents,
 FOREIGN KEY(tenant_id,project_id,graph_id,rebuild_id,candidate_id)
 REFERENCES knowledge.rebuild_candidates(tenant_id,project_id,graph_id,rebuild_id,candidate_id)
);
CREATE TABLE knowledge.snapshot_publications (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 rebuild_id varchar(128) NOT NULL, candidate_id char(32) NOT NULL,
 PRIMARY KEY(tenant_id,project_id,graph_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,rebuild_id,candidate_id)
 REFERENCES knowledge.rebuild_results(tenant_id,project_id,graph_id,rebuild_id,candidate_id)
 DEFERRABLE INITIALLY DEFERRED
);
GRANT SELECT, INSERT ON knowledge.rebuild_intents,knowledge.rebuild_candidates,knowledge.rebuild_results,knowledge.snapshot_publications TO knowledge_service;
GRANT UPDATE(rebuild_id,candidate_id) ON knowledge.snapshot_publications TO knowledge_service;
