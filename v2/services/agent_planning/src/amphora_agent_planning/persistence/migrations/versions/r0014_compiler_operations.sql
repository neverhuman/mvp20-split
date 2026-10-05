CREATE TABLE planning.compiler_rounds (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, selection_id varchar(128) NOT NULL,
 check_id varchar(128) NOT NULL, ordinal integer NOT NULL CHECK(ordinal BETWEEN 1 AND 16),
 expected_count integer NOT NULL CHECK(expected_count BETWEEN 1 AND 64),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,selection_id,check_id),
 UNIQUE(tenant_id,project_id,selection_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,selection_id) REFERENCES planning.compiler_selections
);
CREATE TABLE planning.compiler_effects (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, selection_id varchar(128) NOT NULL,
 effect_id varchar(128) NOT NULL, kind varchar(16) NOT NULL CHECK(kind IN ('save','validate','resolve')),
 check_id varchar(128), descriptor_sha256 char(64),
 effect_sha256 char(64) NOT NULL CHECK(effect_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 1048576),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CHECK((kind='resolve' AND check_id IS NOT NULL AND descriptor_sha256 IS NOT NULL AND descriptor_sha256 ~ '^[0-9a-f]{64}$') OR
       (kind IN ('save','validate') AND check_id IS NULL AND descriptor_sha256 IS NULL)),
 PRIMARY KEY(tenant_id,project_id,selection_id,effect_id),
 UNIQUE(tenant_id,project_id,selection_id,check_id,descriptor_sha256),
 FOREIGN KEY(tenant_id,project_id,selection_id) REFERENCES planning.compiler_selections,
 FOREIGN KEY(tenant_id,project_id,selection_id,check_id) REFERENCES planning.compiler_rounds
);
CREATE UNIQUE INDEX compiler_single_authoring_effect ON planning.compiler_effects(tenant_id,project_id,selection_id,kind)
 WHERE kind IN ('save','validate');
CREATE TABLE planning.compiler_effect_control (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, selection_id varchar(128) NOT NULL,
 effect_id varchar(128) NOT NULL, position integer NOT NULL CHECK(position BETWEEN 1 AND 64),
 PRIMARY KEY(tenant_id,project_id,selection_id,effect_id),
 FOREIGN KEY(tenant_id,project_id,selection_id,effect_id) REFERENCES planning.compiler_effects
);
CREATE TABLE planning.compiler_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, selection_id varchar(128) NOT NULL,
 effect_id varchar(128) NOT NULL, position integer NOT NULL CHECK(position BETWEEN 1 AND 64),
 event_sha256 char(64) NOT NULL CHECK(event_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 2101248),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,selection_id,effect_id,position),
 FOREIGN KEY(tenant_id,project_id,selection_id,effect_id) REFERENCES planning.compiler_effects
);
GRANT SELECT,INSERT ON planning.compiler_rounds,planning.compiler_effects,
 planning.compiler_effect_control,planning.compiler_events TO planning_service;
GRANT UPDATE(position) ON planning.compiler_effect_control TO planning_service;
