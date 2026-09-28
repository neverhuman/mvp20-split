ALTER TABLE runtime.activations ADD COLUMN deadline timestamptz;
ALTER TABLE runtime.attempts ADD COLUMN deadline timestamptz;
UPDATE runtime.attempts SET deadline=lease_expires_at WHERE deadline IS NULL;
ALTER TABLE runtime.attempts ALTER COLUMN deadline SET NOT NULL;
ALTER TABLE runtime.attempts ADD CONSTRAINT attempt_deadline_bound CHECK (lease_expires_at<=deadline);
GRANT UPDATE(deadline) ON runtime.activations TO runtime_service;
