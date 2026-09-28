CREATE TABLE runtime.commands (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, family varchar(128) NOT NULL, command_id varchar(128) NOT NULL,
 operation_id varchar(128) NOT NULL, profile varchar(64) NOT NULL,
 request_sha256 varchar(64) NOT NULL CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK (octet_length(canonical_bytes) <= 262144),
 status varchar(16) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','rejected')),
 receipt jsonb, created_at timestamptz NOT NULL DEFAULT clock_timestamp(), terminal_at timestamptz,
 PRIMARY KEY (tenant_id,project_id,actor_id,family,command_id),
 UNIQUE (tenant_id,project_id,operation_id),
 CHECK ((status='pending' AND receipt IS NULL AND terminal_at IS NULL) OR
        (status<>'pending' AND receipt IS NOT NULL AND terminal_at IS NOT NULL))
);
CREATE TABLE runtime.runs (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 fixture_id varchar(128) NOT NULL, plan_sha256 varchar(64) NOT NULL CHECK (plan_sha256 ~ '^[0-9a-f]{64}$'),
 input_snapshot jsonb NOT NULL CHECK (jsonb_typeof(input_snapshot)='object'),
 status varchar(16) NOT NULL CHECK (status IN ('running','completed','cancelled','failed','blocked')),
 revision bigint NOT NULL DEFAULT 0 CHECK (revision BETWEEN 0 AND 9007199254740991),
 budget_limit bigint NOT NULL CHECK (budget_limit BETWEEN 1 AND 9007199254740991),
 reserved bigint NOT NULL DEFAULT 0 CHECK (reserved BETWEEN 0 AND 9007199254740991),
 spent bigint NOT NULL DEFAULT 0 CHECK (spent BETWEEN 0 AND 9007199254740991),
 PRIMARY KEY (tenant_id,project_id,run_id), CHECK (reserved+spent<=budget_limit)
);
CREATE UNIQUE INDEX runtime_one_active_run ON runtime.runs ((true)) WHERE status='running';
CREATE TABLE runtime.admission_guard (
 singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
 tenant_id varchar(128), project_id varchar(128), run_id varchar(128),
 FOREIGN KEY (tenant_id,project_id,run_id) REFERENCES runtime.runs MATCH FULL
);
INSERT INTO runtime.admission_guard(singleton) VALUES(true);
CREATE TABLE runtime.activations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(128) NOT NULL, invocation_id varchar(128) NOT NULL, specification jsonb NOT NULL,
 status varchar(16) NOT NULL CHECK (status IN ('queued','leased','succeeded','abstained','failed','cancelled','uncertain')),
 current_fence bigint NOT NULL DEFAULT 0 CHECK (current_fence BETWEEN 0 AND 9007199254740991),
 attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 100),
 checkpoint_revision bigint NOT NULL DEFAULT 0 CHECK (checkpoint_revision BETWEEN 0 AND 9007199254740991),
 PRIMARY KEY (tenant_id,project_id,run_id,activation_id),
 UNIQUE (tenant_id,project_id,run_id,invocation_id),
 FOREIGN KEY (tenant_id,project_id,run_id) REFERENCES runtime.runs
);
CREATE TABLE runtime.attempts (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(128) NOT NULL, attempt_id varchar(128) NOT NULL,
 fence bigint NOT NULL CHECK (fence BETWEEN 1 AND 9007199254740991), worker_id varchar(128) NOT NULL,
 lease_expires_at timestamptz NOT NULL,
 status varchar(16) NOT NULL CHECK (status IN ('leased','succeeded','abstained','failed','expired','cancelled','uncertain')),
 settled boolean NOT NULL DEFAULT false,
 PRIMARY KEY (tenant_id,project_id,run_id,attempt_id),
 UNIQUE (tenant_id,project_id,run_id,activation_id,fence),
 UNIQUE (tenant_id,project_id,run_id,activation_id,attempt_id,fence),
 FOREIGN KEY (tenant_id,project_id,run_id,activation_id) REFERENCES runtime.activations
);
CREATE TABLE runtime.completion_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, intent_id varchar(128) NOT NULL,
 run_id varchar(128) NOT NULL, activation_id varchar(128) NOT NULL, attempt_id varchar(128) NOT NULL,
 fence bigint NOT NULL, operation_id varchar(128) NOT NULL,
 semantic_sha256 varchar(64) NOT NULL CHECK (semantic_sha256 ~ '^[0-9a-f]{64}$'),
 output_bindings jsonb NOT NULL, status varchar(16) NOT NULL CHECK (status IN ('prepared','committed','aborted')),
 outcome jsonb,
 PRIMARY KEY (tenant_id,project_id,intent_id), UNIQUE (tenant_id,project_id,operation_id),
 UNIQUE (tenant_id,project_id,intent_id,run_id,activation_id,attempt_id,fence),
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES runtime.commands(tenant_id,project_id,operation_id),
 FOREIGN KEY (tenant_id,project_id,run_id,activation_id,attempt_id,fence)
 REFERENCES runtime.attempts(tenant_id,project_id,run_id,activation_id,attempt_id,fence),
 CHECK ((status='prepared' AND outcome IS NULL) OR (status<>'prepared' AND outcome IS NOT NULL))
);
CREATE TABLE runtime.accepted_completions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, completion_id varchar(128) NOT NULL,
 intent_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL, activation_id varchar(128) NOT NULL,
 attempt_id varchar(128) NOT NULL, fence bigint NOT NULL, result jsonb NOT NULL, reservations jsonb NOT NULL,
 PRIMARY KEY (tenant_id,project_id,completion_id), UNIQUE (tenant_id,project_id,run_id,activation_id),
 UNIQUE (tenant_id,project_id,completion_id,run_id,activation_id),
 FOREIGN KEY (tenant_id,project_id,intent_id,run_id,activation_id,attempt_id,fence)
 REFERENCES runtime.completion_intents(tenant_id,project_id,intent_id,run_id,activation_id,attempt_id,fence)
);
CREATE TABLE runtime.state_revisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(128) NOT NULL, revision bigint NOT NULL CHECK (revision BETWEEN 1 AND 9007199254740991),
 completion_id varchar(128) NOT NULL, checkpoint jsonb NOT NULL,
 PRIMARY KEY (tenant_id,project_id,run_id,activation_id,revision),
 FOREIGN KEY (tenant_id,project_id,completion_id,run_id,activation_id)
 REFERENCES runtime.accepted_completions(tenant_id,project_id,completion_id,run_id,activation_id)
);
CREATE TABLE runtime.worker_policy (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, worker_id varchar(128) NOT NULL,
 revision bigint NOT NULL CHECK (revision BETWEEN 0 AND 9007199254740991), revoked boolean NOT NULL,
 PRIMARY KEY (tenant_id,project_id,worker_id)
);
CREATE TABLE runtime.audit_events (
 event_id varchar(128) PRIMARY KEY, tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 run_id varchar(128) NOT NULL, revision bigint NOT NULL CHECK (revision BETWEEN 0 AND 9007199254740991),
 ordinal integer NOT NULL CHECK (ordinal>=0), payload jsonb NOT NULL,
 UNIQUE (tenant_id,project_id,run_id,revision,ordinal),
 FOREIGN KEY (tenant_id,project_id,run_id) REFERENCES runtime.runs
);
CREATE TABLE runtime.outbox (
 operation_id varchar(128) PRIMARY KEY, event_id varchar(128) NOT NULL REFERENCES runtime.audit_events,
 target varchar(128) NOT NULL, payload jsonb NOT NULL,
 status varchar(16) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','leased','acknowledged')),
 delivery_attempts integer NOT NULL DEFAULT 0 CHECK (delivery_attempts>=0), lease_expires_at timestamptz
);
GRANT SELECT,INSERT ON runtime.commands,runtime.runs,runtime.activations,runtime.attempts,
 runtime.completion_intents,runtime.accepted_completions,runtime.state_revisions,runtime.worker_policy,
 runtime.audit_events,runtime.outbox TO runtime_service;
GRANT SELECT ON runtime.admission_guard TO runtime_service;
GRANT UPDATE(tenant_id,project_id,run_id) ON runtime.admission_guard TO runtime_service;
GRANT UPDATE(status,receipt,terminal_at) ON runtime.commands TO runtime_service;
GRANT UPDATE(status,revision,reserved,spent) ON runtime.runs TO runtime_service;
GRANT UPDATE(status,current_fence,attempt_count,checkpoint_revision) ON runtime.activations TO runtime_service;
GRANT UPDATE(status,lease_expires_at,settled) ON runtime.attempts TO runtime_service;
GRANT UPDATE(status,outcome) ON runtime.completion_intents TO runtime_service;
GRANT UPDATE(revision,revoked) ON runtime.worker_policy TO runtime_service;
GRANT UPDATE(status,delivery_attempts,lease_expires_at) ON runtime.outbox TO runtime_service;
