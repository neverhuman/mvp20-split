ALTER TABLE planning.observations DROP CONSTRAINT observations_canonical_bytes_check;
ALTER TABLE planning.observations ADD CONSTRAINT observations_canonical_bytes_check CHECK (
 octet_length(canonical_bytes) BETWEEN 1 AND 262144 AND
 (octet_length(canonical_bytes) <= 65536 OR
  COALESCE(convert_from(canonical_bytes,'UTF8')::jsonb->'schema_version' = '"2"'::jsonb,false))
);
ALTER TABLE planning.late_observations DROP CONSTRAINT late_observations_canonical_bytes_check;
ALTER TABLE planning.late_observations ADD CONSTRAINT late_observations_canonical_bytes_check CHECK (
 octet_length(canonical_bytes) BETWEEN 1 AND 262144 AND
 (octet_length(canonical_bytes) <= 65536 OR
  COALESCE(convert_from(canonical_bytes,'UTF8')::jsonb->'schema_version' = '"2"'::jsonb,false))
);
