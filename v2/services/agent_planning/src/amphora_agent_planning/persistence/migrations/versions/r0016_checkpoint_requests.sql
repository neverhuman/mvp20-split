ALTER TABLE planning.supervision_commands DROP CONSTRAINT supervision_commands_family_check;
ALTER TABLE planning.supervision_commands ADD CONSTRAINT supervision_commands_family_check
 CHECK (family IN ('planning.supervision.request','planning.supervision.request.v2'));
