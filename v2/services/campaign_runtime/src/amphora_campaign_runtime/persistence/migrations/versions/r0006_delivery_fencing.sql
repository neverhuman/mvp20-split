ALTER TABLE runtime.outbox DROP CONSTRAINT outbox_status_check;
ALTER TABLE runtime.policy_outbox DROP CONSTRAINT policy_outbox_status_check;
ALTER TABLE runtime.outbox ADD CONSTRAINT outbox_status_check CHECK (status IN ('pending','leased','acknowledged','exhausted'));
ALTER TABLE runtime.policy_outbox ADD CONSTRAINT policy_outbox_status_check CHECK (status IN ('pending','leased','acknowledged','exhausted'));
ALTER TABLE runtime.outbox
 ADD COLUMN delivery_token varchar(128),
 ADD COLUMN delivery_generation bigint NOT NULL DEFAULT 0 CHECK (delivery_generation BETWEEN 0 AND 9007199254740991),
 ADD COLUMN available_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 ADD COLUMN created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 ADD COLUMN last_reason varchar(128);
ALTER TABLE runtime.policy_outbox
 ADD COLUMN delivery_token varchar(128),
 ADD COLUMN delivery_generation bigint NOT NULL DEFAULT 0 CHECK (delivery_generation BETWEEN 0 AND 9007199254740991),
 ADD COLUMN available_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 ADD COLUMN created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 ADD COLUMN last_reason varchar(128);
UPDATE runtime.outbox SET status='pending' WHERE status='leased';
UPDATE runtime.policy_outbox SET status='pending' WHERE status='leased';
UPDATE runtime.outbox SET lease_expires_at=NULL;
UPDATE runtime.policy_outbox SET lease_expires_at=NULL;
ALTER TABLE runtime.outbox ADD CHECK ((status='leased') = (delivery_token IS NOT NULL AND lease_expires_at IS NOT NULL));
ALTER TABLE runtime.policy_outbox ADD CHECK ((status='leased') = (delivery_token IS NOT NULL AND lease_expires_at IS NOT NULL));
GRANT UPDATE(delivery_token,delivery_generation,available_at,last_reason) ON runtime.outbox,runtime.policy_outbox TO runtime_service;
CREATE INDEX runtime_outbox_delivery_ready ON runtime.outbox(status,available_at,created_at);
CREATE INDEX runtime_policy_outbox_delivery_ready ON runtime.policy_outbox(status,available_at,created_at);
CREATE INDEX runtime_intent_recovery ON runtime.completion_intents(tenant_id,project_id,run_id,status,intent_id);
