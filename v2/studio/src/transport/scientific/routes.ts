const postPaths = new Set([
  ...["catalog", "entities", "neighborhood", "object"].map(name => "/api/knowledge/v1/graph-explore/" + name),
  ...["catalog", "specimens", "properties", "observation-series"].map(name => "/api/research/v1/research-explore/" + name),
  ...["material-states", "experiments", "observations", "questions", "evidence-needs", "observation-interpretations", "observation-corrections", "material-state-corrections"].map(name => "/api/research/v1/" + name + "/read"),
]);

export function allowedRoute(method: "GET" | "POST", path: string): boolean {
  if (method === "POST") return postPaths.has(path);
  const matched = /^\/api\/data\/v1\/(?:artifacts\/([^/]+)(?:\/(?:content|derivation))?|acquisition\/traces\/([^/]+)|acquisition\/sources\/([^/]+)\/([^/]+))$/.exec(path);
  if (!matched) return false;
  return matched.slice(1).filter(value => value !== undefined).every(encoded => {
    try {
      const value = decodeURIComponent(encoded);
      return value.length <= 128 && /^[A-Za-z0-9][A-Za-z0-9._:-]*$/.test(value) && encodeURIComponent(value) === encoded;
    } catch { return false; }
  });
}
