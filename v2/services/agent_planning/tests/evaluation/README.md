# Evaluation tests

Owner: Planning evaluation module. Run `python -m pytest -c dev/pyproject.toml services/agent_planning/tests/evaluation`. Pure/no SQL or provider. The synthetic rubric is authored independently and checks relationship direction plus source identity. Existing provider fixture supplies only model/limits metadata, never expected results.

Scenarios cover frozen identity/digest, missing/duplicate/foreign repetitions, invalid corpus criteria, malformed output, strict semantic mismatch, authority failure, provider/unknown distinctions and separately bounded abstention. Later runner and live/browser tiers remain distinct. No live model quality claim.
