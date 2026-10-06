ALTER TABLE runtime.supervision_outbox DROP CONSTRAINT supervision_outbox_family_check;
ALTER TABLE runtime.supervision_outbox ADD CONSTRAINT supervision_outbox_family_check
 CHECK (family IN ('planning.supervision.request','planning.supervision.request.v2'));
