import { Ajv2020 } from "ajv/dist/2020.js";
import type { ValidateFunction } from "ajv";
import { numericInput } from "./scalar_input.js";
import type { ValueBinding } from "../../contracts/generated/authoring/save.js";

type Scalar = "string" | "boolean" | "integer" | "number";
export interface SchemaField {
  name: string;
  required: boolean;
  kind: Scalar | "binding";
  reason?: string;
  fixed?: unknown;
  choices?: unknown[];
}
const object = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === "object" && !Array.isArray(value);

/** Bounded fields for a verified object schema; structured values require graph bindings. */
export class SchemaFields {
  private readonly fields: SchemaField[] = [];
  private readonly validators = new Map<string, ValidateFunction>();
  private readonly document: Record<string, unknown>;
  readonly unavailable: string | undefined;

  constructor(document: Readonly<Record<string, unknown>>) {
    this.document = structuredClone(document);
    const root = this.document;
    // Whole-object composition needs a richer editor; do not silently flatten conditional constraints.
    const rootKeys = new Set(["$schema", "$id", "$defs", "title", "description", "type", "properties", "required", "additionalProperties"]);
    if (root.type !== "object" || !object(root.properties) || root.additionalProperties !== false ||
        Object.keys(root).some(key => !rootKeys.has(key)) || Object.keys(root.properties).length > 64 ||
        (root.required !== undefined && (!Array.isArray(root.required) || root.required.some(name => typeof name !== "string")))) {
      this.unavailable = "This schema needs a structured binding editor."; return;
    }
    const required = new Set(root.required as string[] | undefined);
    if ([...required].some(name => !Object.hasOwn(root.properties as object, name))) {
      this.unavailable = "The schema declares an unknown required field."; return;
    }
    const ajv = new Ajv2020({ strict: true, allErrors: false, coerceTypes: false, useDefaults: false, removeAdditional: false });
    for (const [name, raw] of Object.entries(root.properties)) {
      const schema = this.resolve(raw);
      const allowed = new Set(["type", "title", "description", "default", "const", "enum", "minimum", "maximum",
        "exclusiveMinimum", "exclusiveMaximum", "multipleOf", "minLength", "maxLength", "pattern"]);
      if (!schema || !["string", "boolean", "integer", "number"].includes(String(schema.type)) ||
          Object.keys(schema).some(key => !allowed.has(key)) || (Array.isArray(schema.enum) && schema.enum.length > 64)) {
        this.fields.push({ name, required: required.has(name), kind: "binding", reason: "Use a typed graph binding; this field has no scalar editor." }); continue;
      }
      try {
        // Only this resolved scalar reaches AJV: an unsupported sibling cannot poison it.
        const validate = ajv.compile(schema);
        this.validators.set(name, validate);
        this.fields.push({ name, required: required.has(name), kind: schema.type as Scalar,
          ...(Object.hasOwn(schema, "const") ? { fixed: schema.const } : {}),
          ...(Array.isArray(schema.enum) ? { choices: schema.enum } : {}) });
      } catch {
        this.fields.push({ name, required: required.has(name), kind: "binding", reason: "Schema constraints are unsupported by this editor." });
      }
    }
  }

  get snapshot() { return structuredClone({ fields: this.fields, unavailable: this.unavailable }); }

  constant(name: string, text: string): ValueBinding["source"] {
    const field = this.fields.find(item => item.name === name), validate = this.validators.get(name);
    if (this.unavailable || !field || field.kind === "binding" || !validate) throw new Error("Field requires a typed graph binding.");
    let value: string | boolean | number;
    switch (field.kind) {
      case "string": value = text; break;
      case "boolean":
        if (text !== "true" && text !== "false") throw new Error("Choose true or false.");
        value = text === "true"; break;
      default: value = numericInput(text, field.kind);
    }
    if (!validate(value)) throw new Error("Value does not satisfy the reviewed field schema.");
    // A materializer field source, not an uploaded artifact or proof of whole-object compatibility.
    return { kind: field.kind, value } as ValueBinding["source"];
  }

  private resolve(value: unknown): Record<string, unknown> | undefined {
    const seen = new Set<string>();
    for (let depth = 0; depth < 16 && object(value); depth++) {
      if (!("$ref" in value)) return value;
      if (Object.keys(value).length !== 1 || typeof value.$ref !== "string" || !value.$ref.startsWith("#/$defs/") || seen.has(value.$ref)) return undefined;
      seen.add(value.$ref);
      let target: unknown = this.document;
      for (const part of value.$ref.slice(2).split("/")) {
        const key = part.replaceAll("~1", "/").replaceAll("~0", "~");
        target = object(target) && Object.hasOwn(target, key) ? target[key] : undefined;
      }
      value = target;
    }
    return undefined;
  }
}
