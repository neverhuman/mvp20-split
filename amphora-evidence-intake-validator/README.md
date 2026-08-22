# amphora-evidence-intake-validator

Validate returned lab/supplier/model evidence packages.

CLI:

```bash
rtk cargo run --release -- inspect --candidate candidate.json --headless
```

Library API:

```python
from amphora_evidence_intake_validator.score import score
```
