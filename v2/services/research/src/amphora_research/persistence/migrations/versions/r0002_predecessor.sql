ALTER TABLE research.identity_records DROP CONSTRAINT identity_records_check;
ALTER TABLE research.identity_records ADD CONSTRAINT identity_records_predecessor_check
 CHECK((revision=1 AND prior_revision IS NULL)
    OR (revision>1 AND prior_revision IS NOT NULL AND prior_revision=revision-1));
