# amphora-evidence-intake-validator

Validate returned lab/supplier/model evidence packages.

CLI (from the repository root; requires the omitted datasets — see
[`../BUILD.md`](../BUILD.md)):

```bash
cargo run --release -- inspect \
  --candidate amphora-candidate-contract/fixtures/formulation_candidate.json --headless
```
