import { Ajv2020 } from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

export function decoder<T extends object>(schemas: Record<keyof T, object>) {
  const ajv = new Ajv2020({ strict: true, allErrors: false, coerceTypes: false, useDefaults: false, removeAdditional: false });
  ajv.addKeyword({ keyword: "discriminator", schemaType: "object", valid: true });
  addFormats.default(ajv);
  const validators = new Map(Object.entries(schemas).map(([key, schema]) => [key, ajv.compile(schema as object)]));
  return <K extends keyof T>(kind: K, value: unknown): T[K] => {
    if (!validators.get(String(kind))?.(value)) throw new Error("invalid_scientific_contract");
    return value as T[K];
  };
}
