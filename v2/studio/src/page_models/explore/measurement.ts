import type { PropertyViewPage } from "../../contracts/scientific/research.js";
type Value = PropertyViewPage["rows"][number]["value"];
export function measurementText(value: Value): string {
  switch (value.kind) {
    case "numeric": return `${value.quantity.value} ${value.quantity.unit}${value.uncertainty ? `; ${value.uncertainty.description}: ${value.uncertainty.lower.value} ${value.uncertainty.lower.unit} to ${value.uncertainty.upper.value} ${value.uncertainty.upper.unit}` : ""}`;
    case "categorical": return value.label;
    case "missing": return `Missing: ${value.reason}`;
    case "series": return `${value.point_count} points (${value.x_unit}, ${value.y_unit})`;
    case "censored": return [value.lower ? `${value.lower.inclusive ? ">=" : ">"} ${value.lower.quantity.value} ${value.lower.quantity.unit}` : null,
      value.upper ? `${value.upper.inclusive ? "<=" : "<"} ${value.upper.quantity.value} ${value.upper.quantity.unit}` : null].filter(Boolean).join("; ") || "Censored; bounds unavailable";
  }
}
