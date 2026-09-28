ALTER TABLE artifacts.uploads ADD COLUMN created_at timestamptz NOT NULL DEFAULT clock_timestamp();
ALTER TABLE artifacts.upload_attempts DROP CONSTRAINT upload_attempts_status_check;
ALTER TABLE artifacts.upload_attempts ADD CONSTRAINT upload_attempts_status_check
 CHECK (status IN ('streaming','streamed','failed','stale','cleaning','cleaned'));
