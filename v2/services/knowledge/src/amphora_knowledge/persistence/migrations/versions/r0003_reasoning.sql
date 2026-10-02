CREATE TABLE knowledge.reasoning_profiles (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 rule_set_id varchar(128) NOT NULL, version varchar(128) NOT NULL,
 profile_sha256 char(64) NOT NULL CHECK(profile_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 2097152),
 PRIMARY KEY(tenant_id,project_id,graph_id,rule_set_id,version),
 UNIQUE(tenant_id,project_id,graph_id,rule_set_id,version,profile_sha256),
 FOREIGN KEY(tenant_id,project_id,graph_id) REFERENCES knowledge.graph_profiles
);
CREATE TABLE knowledge.reasoning_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 request_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 rule_set_id varchar(128) NOT NULL, version varchar(128) NOT NULL, profile_sha256 char(64) NOT NULL,
 revision bigint NOT NULL, snapshot_sha256 char(64) NOT NULL,
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,graph_id,request_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,rule_set_id,version,profile_sha256)
 REFERENCES knowledge.reasoning_profiles(tenant_id,project_id,graph_id,rule_set_id,version,profile_sha256),
 FOREIGN KEY(tenant_id,project_id,graph_id,revision,snapshot_sha256)
 REFERENCES knowledge.snapshots(tenant_id,project_id,graph_id,revision,snapshot_sha256)
);
CREATE TABLE knowledge.reasoning_decisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 request_id varchar(128) NOT NULL,
 outcome varchar(16) NOT NULL CHECK(outcome IN ('evaluated','failed')),
 decision_sha256 char(64) NOT NULL CHECK(decision_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 20971520),
 decided_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,graph_id,request_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,request_id) REFERENCES knowledge.reasoning_intents
);
GRANT SELECT, INSERT ON knowledge.reasoning_profiles,knowledge.reasoning_intents,knowledge.reasoning_decisions TO knowledge_service;
