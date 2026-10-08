# Internal research-engine demo - October 8, 2026

Audience: internal nontechnical colleagues. Start: **11:00am Central**.
Scope: real local application and retained synthetic campaigns; no new live model
call or scientific worker is needed during the presentation.

## Current scientific execution review

The primary review now serves scientific-live-c at http://127.0.0.1:57013 with
Studio0.20 public-c assets. Start in **Approach and run**: four named scientific
steps, Hansen solvency and Arrhenius viscosity for each of two candidate fixtures,
converge on retained observations. Select a node to inspect its actual result,
calculation steps, input parameters and limits. Candidate A is inside the declared
Hansen sphere; B is outside. No measured compatibility is implied. These are actual
retained tool computations, not animations or renamed numerical evaluations.

**Evaluation design** remains a separate authored proposal with review concerns.
It is not claimed to have generated this run. Explain the next integration step:
runtime LLM proposals composing registered methods and incorporating review feedback.
No scientific validity, molecule generation or synthesis feasibility claim belongs
in this bounded demonstration. Four parallel-eligible tasks do not prove timestamp overlap.

If restarting after the active session ends, use the same Windows user and the
physical deployment root named in Restore.md. Run dev/serve_scientific_review.py
with --run v2/.test-results/scientific-run-c --public v2/.test-results/scientific-ui/public-c,
a new --output directory, --root pointing to that installation, and --open.
The dev virtualenv contains the Deployment controller. Never run two launchers
on the same ports; an exact session-directory STOP file drains the existing one.
Actual served verification is scientific-browser-d; the older preview below is
preserved as a fallback, not the primary scientific walkthrough.

## UI-01 review preview

The updated UI is available as an explicit review preview. Start it with:

```powershell
.\v2\Start-Demo.ps1 -PreviewPublicDirectory Z:\mvp20-split\v2\.test-results\ui01-sme\public-d
```

Start with **Evaluation design**. This is a Codex-authored, unexecuted polymer
proposal, separate from the numerical campaign. Select **Solvency: Hansen screening**
to inspect rationale, input checks, calculation procedure, applicability and gaps.
Select **Compare evidence, then select** to expose the unspecified aggregation rule.
Use **Challenge this step** to record concerns; export/import preserves the exact
design and next-campaign notes. Notes are local/unsubmitted, not automatic LLM input.
This review interaction is the MVP; do not present it as runtime-generated science.

This opens the question-first landing, connected campaign graph and updated
navigation. Select **Approach and run** to view the graph; its root opens
automatically with its parallel evaluation branches visible together. Use **Expand generations**, then the nested branch controls, to inspect repeated work on the same canvas. **Focus expanded work** restores readable scale; **Fit graph** and the overview map navigate the full loaded projection. **Results and evidence** opens the available domain context.
Campaign-wide candidate/generation comparison is still pending UI-01.01.
The preview copies assets into its own session folder; frozen baseline remains
available by launching without the preview option. Use only one launcher at a time.
The older walkthrough below describes that frozen baseline.

## Prepare at 10:45am

Use this Windows computer/user and repository. Docker Desktop must be running with
the accepted restored PostgreSQL/Qdrant containers. Keep the NAS drive connected.
Do not rebuild packages, replace assets or reset databases immediately before presenting.
The launcher checks the qualified asset hashes and fails if they changed.
It uses frozen-original/frozen-successor manifests with copies of all seven owner
lockfiles, so subsequent working-tree dependency updates do not repin the demo.

From PowerShell:

```powershell
cd Z:\mvp20-split
.\v2\Start-Demo.ps1
```

Allow startup time; the browser opens when owners and gateway are ready. Keep the
terminal open. The default duration is 24 hours after startup. A plain bookmark
does not create a session: rerun the launcher to get a fresh one-time browser ticket.
Do not run two launchers together. Ctrl+C stops and drains the selected services.
Wait for **Demo stopped; owners drained successfully** before restarting.

## Eight-minute walkthrough

1. **Why this exists (one minute).** "Research usually spreads across scripts,
   models, data and notes. We are building a system that makes the steps and their
   evidence inspectable, so the next experiment can build on what was learned."
2. **Show the research pathway (two minutes).** In Execution choose **Authored graph**.
   Explain tools as steps and the graph as their composition. Click **Root graph** in Occurrence groups to load the connected graph; use those
   groups to inspect repeated work. Activation inventory is an execution list,
   not the connected authored pathway. This campaign has already run; the browser
   is reading its retained history.
3. **Show the AI's bounded role (one minute).** Return to **Activation inventory**,
   select **Inspect checkpoint reasoning**, then **review-numeric-seed**,
   **Inspect request 1**, **Context** and **Responses**. This recorded model
   abstained. Explain that refusing to overclaim is a valid outcome; we retained
   the context and decision rather than fabricating scientific progress.
4. **Show the evidence (two minutes).** Open **Domain and evidence**, select
   **Bounded numeric search**, then the relationship/claim. Inspect its source
   passage. A graph relationship is a scoped claim, not automatically a proven fact.
5. **Choose the next question (two minutes).** Open **Question & feedback**, then
   **Quality points** and select a point. Enter an **Intended improvement** and
   **What do you expect to learn?**, choose **Save focus**, then **Export next-campaign
   focus**. The file is a local unsubmitted draft. The present record has no selected
   assessment; the UI says so. Explicit AI criterion targeting is approved next work.

## Optional successor comparison

The screenshot fallback includes the actual corrected source and successor lineage.
Use those for an uninterrupted comparison. For interactive successor inspection,
stop the original launcher and wait for its successful drain, then run:

```powershell
.\v2\Start-Demo.ps1 -Scenario successor
```

Execution - Authored graph - first occurrence group - Named research views ?
Inspect predecessor lineage shows the retained link to the original campaign.
Domain and evidence opens the corrected domain revision. Select its claim and
source passage to show that the newer interpretation remains unresolved and the
original history is preserved. This is a completed successor, not a newly generated
proposal from the focus draft you just exported.

## Fallback and boundaries

Open `Z:\mvp20-split\v2\docs\Demo\2026-10-08\index.html` in the browser
for labeled screenshots from actual-owner qualification. It works without running
APIs and clearly identifies retained screenshots. One repeated rehearsal hit a failed feedback read; its cause remains unresolved.
If a view fails, use the corresponding screenshot rather than relying on recovery
during the talk. If launch fails, use this instead
of debugging services during the presentation. No screenshots represent a live run.

Demonstrated: composed execution, repeated work, retained model context/decision,
knowledge/source inspection, local focus export and corrected successor lineage.
Still in progress: automatic criterion-targeted AI follow-up, dependable fresh runs
after intermittent worker faults, and qualified polymer/biology examples. Avoid
claiming scientific discovery, arbitrary autonomous graph generation or production readiness.

Shutdown does not remove databases, artifacts or previous campaign histories. The
launcher prints a session folder; its ready/evidence files record startup and drain
without credentials. If the terminal is lost, do not start another copy until the
existing owned processes have stopped.
