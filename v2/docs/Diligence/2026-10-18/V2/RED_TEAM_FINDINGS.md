# Amphora | Candid red-team findings - version 2

Local preparer reviewed actual V1 PDF, task ledger and code; additional worker reviewed reconciliation only after Library access denial. Not independent scientific validation or legal opinion.

Confirmed defects, evidence gaps and unknowns have different meanings. Missing evidence is unverified, not declared false. Severity concerns diligence or the stated trusted-tooling profile, not a remotely exposed production service.

## RF-01 - Mutable hashes could launder a substituted historical checker

**Severity:** high. **Basis:** confirmed_code_defect. **Disposition:** resolved_in_scoped_local_tests.

**Investor impact:** A fake twelve-gate checker was accepted after its mutable mapping/manifest hashes were recomputed. This invalidates any claim that V1 necessarily ran the original assertions under such tampering.

**Concrete fix:** Fixed reviewed policy hashes and exact payload allowlist are checked before execution; full original gate/profile/limitation semantics checked; use reviewed Git verifier and optional externally obtained manifest digest.

**Verification / remaining evidence:** A coordinated fake-checker substitution with mutable hashes recomputed must reject before execution.

Source: [v2/dev/diligence/capsule.py at e1198952, lines 47-85](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/dev/diligence/capsule.py#L47). SHA-256 `d99d67f4a199f314112078df81a828960f9568b83652e3b572b4d3ceba525238`.

## RF-02 - A README could qualify an owner approval task

**Severity:** high. **Basis:** confirmed_code_defect. **Disposition:** resolved_in_scoped_local_tests.

**Investor impact:** V1 accepted DD-010 as verified when its only evidence was the root README; evidence existence was mistaken for acceptance.

**Concrete fix:** Evidence registry binds bytes, supported task IDs, result/exit status and current verifier code; protected role-approval tasks cannot be auto-promoted by preparer records.

**Verification / remaining evidence:** README-only promotion, failed receipt and stale code binding reject.

Source: [v2/dev/diligence/core.py at e1198952, lines 197-248](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/dev/diligence/core.py#L197). SHA-256 `4f37206b301f6af2d5f5631d9a72ff53a78badd999177a4bcb1269d5b7ae8a23`.

## RF-03 - 93 tasks and preparation percentages obscure the investment decision

**Severity:** high. **Basis:** confirmed_presentation_issue. **Disposition:** implemented.

**Investor impact:** The 27-page packet showed 27.96% implementation and 26.88% verification for a mixed future register; these quantities do not measure scientific, product or commercial derisking.

**Concrete fix:** Retain the 93 task IDs as a backlog; lead V2 with one current-state page and five decision tracks. Remove task-count readiness percentages and unjustified uniform effort ranges.

**Verification / remaining evidence:** Current-state and decision validators report zero investment gates met, with separate technical receipts.

Source: [v2/docs/Diligence/2026-10-18/PROGRESS.md at e1198952, lines 1-19](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/docs/Diligence/2026-10-18/PROGRESS.md#L1). SHA-256 `96d1adacb9740a368db388f03fcb2180805c12d2e7015b0c8bd4069a1e1ece2a`.

## RF-04 - The benchmark has not qualified the deployed product

**Severity:** high. **Basis:** evidence_gap. **Disposition:** disclosed_future_proof.

**Investor impact:** The PLGA study is an isolated adapter, while owner/curation/recovery examples are different synthetic/historical scenarios.

**Concrete fix:** Explicit exercise matrix and DG-2 frozen integration gate; no claim of an end-to-end PLGA engine run.

**Verification / remaining evidence:** Every scientific proof card says isolated adapter/no LLM; an integration claim requires its own actual-owner evidence.

Source: [v2/docs/Diligence/2026-10-18/WORKPLAN.md at e1198952, lines 51-75](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/docs/Diligence/2026-10-18/WORKPLAN.md#L51). SHA-256 `bbe06ecce45a313e0ecfc3f41202b63008260e90f05850b8907321f531d4fd5e`.

## RF-05 - No independent scientific lift or transfer is established

**Severity:** high. **Basis:** evidence_gap. **Disposition:** disclosed_future_proof.

**Investor impact:** All ten planned stage-2 intervals include zero on a development-exposed corpus. Neither replay nor new formatting creates external validation.

**Concrete fix:** Retain full inference beside scientific proof cards; define DG-4 frozen new-panel/margin/replicate gate and unfavorable-result branch.

**Verification / remaining evidence:** No winner badge or ROI inference; all 12 cells and 10 contrasts remain linked unchanged.

Source: [docs/review/plga/evidence/evidence_summary.json at e1198952, lines 1-284](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/docs/review/plga/evidence/evidence_summary.json#L1). SHA-256 `54f87966c2aceea80456fc570ce62eb10af901a0ab281abc378f7cc68672a412`.

## RF-06 - No measured buyer value or willingness to pay

**Severity:** high. **Basis:** commercial_unknown. **Disposition:** disclosed_future_proof.

**Investor impact:** Workflow composition/provenance could be valuable, but there is no documented buyer interview, matched value study, adoption evidence or pricing evidence.

**Concrete fix:** Commercial hypothesis ledger, current-alternative comparison and DG-3 decision protocol; unknown thresholds remain blocking and unestimated.

**Verification / remaining evidence:** No customer/pricing/savings invented; primary value metric and decision margin must be frozen before a pilot.

Source: [v2/docs/Diligence/2026-10-18/WORKPLAN.md at e1198952, lines 269-313](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/docs/Diligence/2026-10-18/WORKPLAN.md#L269). SHA-256 `bbe06ecce45a313e0ecfc3f41202b63008260e90f05850b8907321f531d4fd5e`.

## RF-07 - License/provenance is not a chain-of-rights conclusion

**Severity:** high. **Basis:** rights_unknown. **Disposition:** disclosed_requires_owner.

**Investor impact:** Public visibility, existing proprietary terms and data attribution do not prove exclusive ownership or permission for every proposed reuse.

**Concrete fix:** Contribution/provenance matrix, payload rights gate and candid unresolved ownership status; keep existing terms and original attribution.

**Verification / remaining evidence:** Review each selected object, not a blanket claim that this packet resolves rights or patentability.

Source: [v2/docs/Diligence/2026-10-18/DECISIONS.md at e1198952, lines 1-23](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/docs/Diligence/2026-10-18/DECISIONS.md#L1). SHA-256 `9b2af6e8cde5f1a88efe912634dc6a16d38ac3d4cf4ac8126e2154e9c6ef0431`.

## RF-08 - The moat is a hypothesis and adjacent foundations already exist

**Severity:** medium. **Basis:** differentiation_unknown. **Disposition:** disclosed_future_proof.

**Investor impact:** Workflow provenance and stateful agent orchestration are established adjacent capabilities. The packet does not prove competitor absence or exclusivity.

**Concrete fix:** Primary-source AiiDA/LangGraph acknowledgement and contribution-specific matrix; measure claimed integration/value rather than marketing a universal first.

**Verification / remaining evidence:** No unsupported world-first/patent/moat assertion; source-backed present mechanism distinct from future commercial advantage.

Source: [v2/docs/Diligence/2026-10-18/WORKPLAN.md at e1198952, lines 184-205](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/docs/Diligence/2026-10-18/WORKPLAN.md#L184). SHA-256 `bbe06ecce45a313e0ecfc3f41202b63008260e90f05850b8907321f531d4fd5e`.

## RF-09 - Checker subprocesses were weakly bounded and checks repeated

**Severity:** medium. **Basis:** confirmed_code_defect. **Disposition:** resolved_in_scoped_local_tests.

**Investor impact:** capture_output was memory-unbounded, parser accepted only the last output line, and verify-source ran capsule checks twice.

**Concrete fix:** Bound stdout/stderr, reject malformed whole JSON, use a shared deadline and isolated child Python, and run the required capsule pass once.

**Verification / remaining evidence:** Output flood, timeout, leading garbage JSON and duplicate execution regression cases fail safely.

Source: [v2/dev/diligence/capsule.py at e1198952, lines 27-39](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/dev/diligence/capsule.py#L27). SHA-256 `d99d67f4a199f314112078df81a828960f9568b83652e3b572b4d3ceba525238`.

## RF-10 - Task/JSON shape and pointer validation had gaps

**Severity:** medium. **Basis:** confirmed_code_defect. **Disposition:** resolved_in_scoped_local_tests.

**Investor impact:** Null arrays and wrong shapes could escape clean rejection; source ranges/phase membership and canonical array selectors were insufficiently checked.

**Concrete fix:** Stricter collection/phase/evidence validation and canonical JSON-pointer array indexes; fixed safe CLI error output.

**Verification / remaining evidence:** Null/malformed arrays, wrong phase membership, negative index and bad pointer escapes reject.

Source: [v2/dev/diligence/core.py at e1198952, lines 102-111](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/dev/diligence/core.py#L102). SHA-256 `4f37206b301f6af2d5f5631d9a72ff53a78badd999177a4bcb1269d5b7ae8a23`.

## RF-11 - Output aliases could evade the checkout exclusion

**Severity:** medium. **Basis:** confirmed_path_gap. **Disposition:** resolved_in_scoped_local_tests.

**Investor impact:** V1 used absolute paths and checked only the immediate output parent; an ancestor symlink could point back into the checkout.

**Concrete fix:** Resolve output paths before checkout/inside-capsule checks and reject existing/linked destinations. Keep the trusted-directory/TOCTOU limit explicit.

**Verification / remaining evidence:** Ancestor link into repository, existing output and archive-inside-payload aliases reject without overwriting.

Source: [v2/dev/diligence/cli.py at e1198952, lines 58-69](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/dev/diligence/cli.py#L58). SHA-256 `2b9f007af31adbbca71074ef5bb1eed8b6b26ca7ffee3701fbff995c03d44b98`.

## RF-12 - Historical pass labels could be mistaken for current readiness

**Severity:** medium. **Basis:** confirmed_scope_gap. **Disposition:** resolved_in_scoped_local_tests.

**Investor impact:** A fresh receipt check validates old assertions; it does not rerun old process/recovery scenarios or assess current installed service health.

**Concrete fix:** Reports enumerate executed, historical-only and omitted checks; DG-2 requires current installed-owner proof separately.

**Verification / remaining evidence:** Source and capsule scope fields differ correctly; no historical pass is labeled fresh process execution.

Source: [v2/dev/diligence/capsule.py at e1198952, lines 89-102](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/dev/diligence/capsule.py#L89). SHA-256 `d99d67f4a199f314112078df81a828960f9568b83652e3b572b4d3ceba525238`.

## RF-13 - Roles and effort ranges do not establish staffing or budget

**Severity:** medium. **Basis:** accountability_unknown. **Disposition:** implemented.

**Investor impact:** A named role is not an assigned person. Uniform task-minute estimates and a six-hour aspiration do not establish delivery capacity.

**Concrete fix:** Unassigned roles and unapproved budgets are explicit at every decision track; remove uncalibrated effort ranges and schedule promises.

**Verification / remaining evidence:** Activation of future work needs named ownership, a frozen scope and an approved budget; current task authorizes only bounded revision/publication.

Source: [v2/docs/Diligence/2026-10-18/task_ledger.json at e1198952, lines 1-80](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/docs/Diligence/2026-10-18/task_ledger.json#L1). SHA-256 `6d254b53cebbd98339c021872ea8379c97af6eb03597156e1d7d9c700657b6c5`.

## RF-14 - The additional reviewer did not inspect the delivered artifacts

**Severity:** medium. **Basis:** review_limit. **Disposition:** implemented.

**Investor impact:** The independent worker was denied Library artifact access and reviewed only supplied reconciliation. It cannot be called an independent full-PDF/code audit.

**Concrete fix:** Separate review coverage statement; local preparer inspected actual artifacts and ran the confirmed code probes.

**Verification / remaining evidence:** Review credits state precisely which material was and was not accessible.

Source: [v2/docs/Diligence/2026-10-18/HANDOFF.md at e1198952, lines 1-32](https://github.com/neverhuman/mvp20-split/blob/e11989526739ec4a3282416e2e4acf775effb104/v2/docs/Diligence/2026-10-18/HANDOFF.md#L1). SHA-256 `6c9140c405e36354e239e6a63b2cf877e742053ed25c4fa6182449258cdcf1d4`.
