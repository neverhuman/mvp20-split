CREATE TABLE runtime.policy_audit_events (
 event_id varchar(128) PRIMARY KEY,
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 worker_id varchar(128) NOT NULL, revision bigint NOT NULL CHECK (revision>=0),
 operation_id varchar(128) NOT NULL UNIQUE, payload jsonb NOT NULL,
 FOREIGN KEY (tenant_id,project_id,worker_id) REFERENCES runtime.worker_policy,
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES runtime.commands(tenant_id,project_id,operation_id)
);
CREATE TABLE runtime.policy_outbox (
 operation_id varchar(128) PRIMARY KEY, event_id varchar(128) NOT NULL REFERENCES runtime.policy_audit_events,
 target varchar(128) NOT NULL, payload jsonb NOT NULL,
 status varchar(16) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','leased','acknowledged')),
 delivery_attempts integer NOT NULL DEFAULT 0 CHECK (delivery_attempts>=0), lease_expires_at timestamptz
);
GRANT SELECT,INSERT ON runtime.policy_audit_events,runtime.policy_outbox TO runtime_service;
GRANT UPDATE(status,delivery_attempts,lease_expires_at) ON runtime.policy_outbox TO runtime_service;
