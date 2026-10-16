# Scientific qualification and evidence claims

This is the verification workflow for a scientific claim, used with [testing and coverage](Testing_and_Coverage.md). [Product acceptance](../../Architecture/Requirements/Product_Requirements.md#acceptance-posture) and the owning domain retain their authority; this checklist does not promote a result.

1. Name the claim, representation, units, domain applicability and intended use. Distinguish measured, simulated, predicted and model-inferred outputs.
2. Pin source/data/model/method versions, preprocessing and relevant scope/rights. Keep raw evidence, conversions and accepted revisions attributable.
3. Choose the relevant baseline, independent test oracle, negative/failure controls and acceptance gate before interpreting the result. Keep comparison populations and split protocols explicit; report transfer limitations instead of treating within-corpus success as novel-chemistry validation.
4. Retain uncertainty, abstentions, exclusions, contradictory evidence and failures alongside useful outputs. Missing or ineligible evidence is not a zero score. Report what was actually measured and the limits of the test.
5. Separate successful execution, engineering correctness, scientific validity and external qualification. Passing tests, signed receipts, a completed campaign or an attractive error metric cannot substitute for the required scientific evidence/review.
6. Record the evidence and disposition in the owning module/plan/audit record. Preserve prior outcomes and explicit correction/supersession history; changes do not silently repin active campaigns.

Synthetic fixtures can prove bounded engineering behavior while scientific data remain unavailable. They must remain labeled as fixtures. Weak or uncertain science does not automatically block valid exploratory execution; explicit prerequisites and authority gates still apply.
