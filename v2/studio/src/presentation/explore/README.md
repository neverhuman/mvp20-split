# Scientific Explore workspace

UI-01.05 adds embedded presentation for the connected campaign's distinct Knowledge
tab. Embedded mode omits the duplicate app header and uses a section beneath the
owning main landmark; the same ExploreModel remains the sole scientific read owner.
No alternate source viewer or relaxed integrity/media checks are introduced.

BP-06.06/B2.02-.04, Studio0.7. Internal researcher task: search a pinned domain graph, inspect a qualified claim and follow exact source/conversion evidence; switch to the selected experiment's specimens and reported properties. The host supplies and disposes ExploreModel with explicit pins. No global project picker, deployed gateway, scientific mutation or live campaign intervention is implemented here.

`workspace.tsx` owns visible view choice and document/view lifecycle; hidden region requests are cancelled and cleared. It subscribes to one model snapshot and never fetches. `domain.tsx` uses bounded search/neighborhood pages, a reusable GraphCanvas, keyboard concept lists and explicit assertion links. The pure Explore scene projection draws only owner-declared edges between exact returned entity revisions; panning/layout never changes scientific topology. Counts describe omissions from the loaded graph window, not viewport clipping.

`laboratory.tsx` displays specimen/preparation identities, original measurement strings/units/censor bounds/uncertainty, missing reasons, declared context links and quality flags. Series preserve order and repeated coordinates. Selecting result evidence replaces the previous claim's inspector selection. It does not score scientific quality or infer comparability. Question/need/correction progression belongs to the separate feedback panel.

`inspection.tsx` renders qualified assertions, exact verified source spans, pinned conversion history, Artifact metadata and retained derivation inputs. Source strings render as escaped text. Metadata is distinct from current content authorization; failed hashes never produce verified passages. Hypothesis/retraction/unknown controls remain explicit, not global execution vetoes. `status.tsx` renders named loading/empty/partial/stale/denied/unavailable/failure states. Styling extends shared Studio tokens, with one growing view and selection inspector; scientific tables/canvas own intentional local overflow while the document fits narrow viewports.

Verification: `npm run test:explore` builds and runs scripted public-owner HTTP in Chromium. It covers keyboard graph->claim->source->conversion, specimen/property/series traversal, evidence replacement, denied and corrupted content, empty/offline/paged/long labels and hidden late requests. Desktop1440 and narrow390 screenshots are reviewed; Axe A/AA and document overflow pass. `dev/verify_studio.py --explore-browser` independently installs locked Node dependencies and retains its browser evidence. Actual installed-owner transport/model tests are a separate tier. BP-06.06/B3 verifies actual browser-to-owner traversal, durable projection reconstruction and independent Studio installation; reconstruction preserves synthetic records without validating their science. No instrumented React coverage or full assistive-technology conformance is claimed.

Replacement preserves source-adjacent model/transport contracts, exact revision/context meaning, visible qualification, cancellation/denial clearing, escaped source text, bounded counts and accessible alternative navigation. Shared Monitor/Draft behavior remains independently owned.

Optional Question & feedback mode is owned by [feedback presentation](../feedback/README.md) and its separate page model. Host supplies compatible pinned context. Switching modes suspends inactive loaders; feedback refresh/denial clears linked inspector state.


`comparison.tsx` renders two explicit observations from bounded, same-experiment specimen/property pages. Accessible selectors, original values, prepared-state/sample differences and quality flags remain visible; incomplete context is not filled from a nominal candidate. Context identity and same-record status do not authorize reuse. The single growing table links selected result/preparation evidence to the inspector. Page changes and selection changes clear unrelated detail.

`material.tsx` shows an exact Research material revision and eight preparation events per window, including reported/proposed attribution, method, duration, atmosphere and expandable condition values. It displays the retained feature count; it does not implement a feature-editing surface. A new material revision resets paging. Current denial clears comparison and inspector through the shared model. Optional record-client absence is explicit unavailable.

Comparison browser acceptance includes same candidate/different80/120degree preparation, preserved quality flags, explicit8-step paging, denial and narrow/desktop accessibility/overflow. The public HTTP fixture is synthetic; actual two-specimen owner progression and reuse rejection passed the separate B2.04c/d gates. Module replacements retain model-owned reads and the existing token/layout system.

Local hosting can pass `active=false` to suspend Explore reads while preserving
mounted local controls. Effective visibility combines this flag with document
visibility; returning refreshes the selected owner projection. Default remains active.

SQ-01 optionally passes a host-owned QualityLinkModel into FeedbackPanel. Its reads
follow feedback visibility; independent Runtime denial removes the output link
without granting or denying separately authorized scientific records. No inferred
consumer index or mutation is introduced.
