CREATE TABLE runtime.intent_retention_closures (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 intent_id varchar(128) NOT NULL, output_binding varchar(128) NOT NULL,
 receipt jsonb NOT NULL CHECK(jsonb_typeof(receipt)='object'),
 PRIMARY KEY(tenant_id,project_id,intent_id,output_binding),
 FOREIGN KEY(tenant_id,project_id,intent_id,output_binding) REFERENCES runtime.intent_reservations
);
GRANT SELECT,INSERT ON runtime.intent_retention_closures TO runtime_service;
