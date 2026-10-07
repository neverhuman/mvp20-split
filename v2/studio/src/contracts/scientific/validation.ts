import type { ValidateFunction } from 'ajv';

export function decoder<T extends object>(compiled: Record<string, ValidateFunction>) {
  const validators = new Map(Object.entries(compiled));
  return <K extends keyof T>(kind: K, value: unknown): T[K] => {
    if (!validators.get(String(kind))?.(value)) throw new Error("invalid_scientific_contract");
    return value as T[K];
  };
}

export function referenceDecoder<T>(validate: ValidateFunction) {
  return (value: unknown): T => {
    if (!validate(value)) throw new Error("invalid_scientific_reference");
    return value as T;
  };
}
