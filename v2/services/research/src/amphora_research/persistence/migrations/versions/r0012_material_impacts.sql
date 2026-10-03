-- Block concurrent decision writes across backfill/trigger installation. Old writer
-- packages also receive atomic index maintenance after the migration commits.
LOCK TABLE research.scientific_decisions IN SHARE ROW EXCLUSIVE MODE;
CREATE TABLE research.decision_material_states (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 kind varchar(16) NOT NULL CHECK(kind='eligibility'), decision_id varchar(128) NOT NULL,
 state_id varchar(128) NOT NULL, state_revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,kind,decision_id),
 FOREIGN KEY(tenant_id,project_id,kind,decision_id) REFERENCES research.scientific_decisions,
 FOREIGN KEY(tenant_id,project_id,state_id,state_revision) REFERENCES research.material_state_revisions
);
CREATE INDEX decision_material_impact ON research.decision_material_states(tenant_id,project_id,state_id,state_revision,kind,decision_id);
DO $audit$
BEGIN
 IF EXISTS (
  SELECT 1 FROM research.scientific_decisions
  WHERE kind='eligibility'
   AND (convert_from(canonical_bytes,'UTF8')::jsonb #>> '{assessment,policy,context,subject,material_state,material_state_id}') IS NOT NULL
   AND ((convert_from(canonical_bytes,'UTF8')::jsonb #>> '{assessment,policy,context,subject,material_state,scope,tenant_id}') IS DISTINCT FROM tenant_id
     OR (convert_from(canonical_bytes,'UTF8')::jsonb #>> '{assessment,policy,context,subject,material_state,scope,project_id}') IS DISTINCT FROM project_id)
 ) THEN RAISE EXCEPTION 'existing_decision_material_state_scope_mismatch'; END IF;
END;
$audit$;
INSERT INTO research.decision_material_states(tenant_id,project_id,kind,decision_id,state_id,state_revision)
 SELECT tenant_id,project_id,kind,decision_id,
  (convert_from(canonical_bytes,'UTF8')::jsonb #>> '{assessment,policy,context,subject,material_state,material_state_id}'),
  (convert_from(canonical_bytes,'UTF8')::jsonb #>> '{assessment,policy,context,subject,material_state,revision}')::bigint
 FROM research.scientific_decisions
 WHERE kind='eligibility'
 AND (convert_from(canonical_bytes,'UTF8')::jsonb #>> '{assessment,policy,context,subject,material_state,material_state_id}') IS NOT NULL;

CREATE FUNCTION research.index_decision_material_state() RETURNS trigger LANGUAGE plpgsql AS $function$
DECLARE state_ref jsonb;
BEGIN
 IF NEW.kind='eligibility' THEN
  state_ref := convert_from(NEW.canonical_bytes,'UTF8')::jsonb #> '{assessment,policy,context,subject,material_state}';
  IF state_ref IS NOT NULL AND state_ref <> 'null'::jsonb THEN
   IF state_ref #>> '{scope,tenant_id}' IS DISTINCT FROM NEW.tenant_id
      OR state_ref #>> '{scope,project_id}' IS DISTINCT FROM NEW.project_id THEN
    RAISE EXCEPTION 'decision_material_state_scope_mismatch';
   END IF;
   INSERT INTO research.decision_material_states(tenant_id,project_id,kind,decision_id,state_id,state_revision)
    VALUES(NEW.tenant_id,NEW.project_id,NEW.kind,NEW.decision_id,state_ref->>'material_state_id',(state_ref->>'revision')::bigint);
  END IF;
 END IF;
 RETURN NEW;
END;
$function$;
REVOKE ALL ON FUNCTION research.index_decision_material_state() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION research.index_decision_material_state() TO research_service;
CREATE TRIGGER index_decision_material_state AFTER INSERT ON research.scientific_decisions
 FOR EACH ROW EXECUTE FUNCTION research.index_decision_material_state();
GRANT SELECT,INSERT ON research.decision_material_states TO research_service;
