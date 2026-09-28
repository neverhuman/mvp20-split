CREATE TABLE registry.commands (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 family varchar(128) NOT NULL, command_id varchar(128) NOT NULL, operation_id varchar(128) NOT NULL,
 request_sha256 varchar(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'), canonical_bytes bytea NOT NULL,
 receipt jsonb NOT NULL CHECK(jsonb_typeof(receipt)='object'), created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,actor_id,family,command_id), UNIQUE(tenant_id,project_id,operation_id)
);
CREATE TABLE registry.releases (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 capability_id varchar(128) NOT NULL, release varchar(128) NOT NULL, contract_version varchar(128) NOT NULL,
 descriptor_sha256 varchar(64) NOT NULL CHECK(descriptor_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL, descriptor jsonb NOT NULL, lock_entry jsonb NOT NULL,
 PRIMARY KEY(tenant_id,project_id,capability_id,release,contract_version),
 UNIQUE(tenant_id,project_id,descriptor_sha256)
);
CREATE TABLE registry.release_states (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, descriptor_sha256 varchar(64) NOT NULL,
 revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 status varchar(16) NOT NULL CHECK(status IN ('registered','active','draining','revoked')),
 PRIMARY KEY(tenant_id,project_id,descriptor_sha256),
 FOREIGN KEY(tenant_id,project_id,descriptor_sha256) REFERENCES registry.releases(tenant_id,project_id,descriptor_sha256)
);
CREATE TABLE registry.deployments (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, deployment_id varchar(128) NOT NULL,
 descriptor_sha256 varchar(64) NOT NULL, definition jsonb NOT NULL,
 revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 status varchar(16) NOT NULL CHECK(status IN ('active','draining','revoked')),
 PRIMARY KEY(tenant_id,project_id,deployment_id),
 FOREIGN KEY(tenant_id,project_id,descriptor_sha256) REFERENCES registry.releases(tenant_id,project_id,descriptor_sha256)
);
CREATE TABLE registry.replicas (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, deployment_id varchar(128) NOT NULL,
 replica_id varchar(128) NOT NULL, worker_id varchar(128) NOT NULL,
 revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 free_slots integer NOT NULL CHECK(free_slots BETWEEN 0 AND 1024),
 observed_at timestamptz NOT NULL, expires_at timestamptz NOT NULL,
 PRIMARY KEY(tenant_id,project_id,deployment_id,replica_id),
 FOREIGN KEY(tenant_id,project_id,deployment_id) REFERENCES registry.deployments,
 CHECK(expires_at>observed_at AND expires_at<=observed_at+interval '60 seconds')
);
CREATE TABLE registry.audit_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, operation_id varchar(128) NOT NULL,
 payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,operation_id),
 FOREIGN KEY(tenant_id,project_id,operation_id) REFERENCES registry.commands(tenant_id,project_id,operation_id)
);
GRANT SELECT,INSERT ON registry.commands,registry.releases,registry.release_states,registry.deployments,
 registry.replicas,registry.audit_events TO registry_service;
GRANT UPDATE(revision,status) ON registry.release_states,registry.deployments TO registry_service;
GRANT UPDATE(revision,free_slots,observed_at,expires_at) ON registry.replicas TO registry_service;
