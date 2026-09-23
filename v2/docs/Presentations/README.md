# Internal Engine Presentation

- Status: 14-slide internal explainer complete; target architecture distinguished from source-reviewed implementation
- Last refreshed: `2026-09-16 14:47:37`
- Audience: internal management and scientific/product stakeholders; no technical background assumed
- Scope: dynamic execution graphs, materials/biology composition, scoped data, human control, evolutionary reuse, and first delivery proofs
- Validation: opened and exported with PowerPoint 16.0; all 14 slides rendered; text overflow check passed after layout corrections

## Deliverables

- [Editable PowerPoint](../Artifacts/INTERNAL_ONLY-AMPHORA_Research_Engine_Internal.pptx)
- [PDF reading copy](../Artifacts/AMPHORA_Research_Engine_Internal.pdf)
- [Reproducible slide builder](build_internal_engine_deck.py)

All diagrams and text are editable PowerPoint shapes. Every slide is marked internal-only and carries presenter notes. Target-state diagrams and the conceptual Graph Studio view are illustrative; they are not screenshots or claims of implemented functionality. The source-review slide describes implementation separately. The deck does not repeat unverified regulatory, clinical, financial, or filing-timeline claims from the product brief.

## Narrative

1. Research pathways that adapt.
2. From a research question to an evidence trail.
3. Two authored maps and a derived execution record.
4. Branching, feedback, and human review in a dynamic campaign.
5. Materials, drug-delivery, and biological capabilities in different compositions.
6. Domain/product/project data sources and retained inputs.
7. Biological context and scientific applicability.
8. Candidate-parameter search versus future pathway evolution.
9. Human Graph Studio as an inspection and intervention surface.
10. Reuse, adaptation, and new implementation/validation needs.
11. The five proposed products mapped to shared tools and distinct evidence.
12. Retained failures, comparison, and reviewed reuse.
13. Delivery gates without calendar promises.
14. Internal alignment and the first portability proof.

## Source of Truth

- [Graph-native architecture](../Architecture/Graph_Native_Research_Engine.md)
- [Product requirements](../Architecture/Product_Requirements.md)
- [Data sources and acquisition](../Architecture/Data_Sources_and_Acquisition.md)
- [Evolutionary code reuse baseline](../Architecture/Evolutionary_Code_Reuse_Baseline.md)
- Product examples: `docs/Artifacts/AMPHORA_Top5_Product_Brief_1.docx`

To rebuild, install `python-pptx` and run `py -3 docs/Presentations/build_internal_engine_deck.py` from the repository root. The script regenerates the PPTX at its named output path; re-export the PDF from PowerPoint after any changes. Rendering review used PowerPoint's native PDF and PNG exports. Temporary slide previews are outside the repository.

## Investor Positioning Deck

### Presenter-led visual version

- Status: three diagram-led slides complete; native PowerPoint rendering and text overflow checks passed
- Last refreshed: `2026-09-18 14:58:20`
- Scope: why build, the connected engine, and human navigation/editing with evolving research pathways

[Visual PowerPoint](../Artifacts/AMPHORA_Engine_VC_Visual_v3.pptx) | [PDF](../Artifacts/AMPHORA_Engine_VC_Visual_v3.pdf) | [Builder](build_vc_visual_v3.py)

Large editable diagrams and short labels carry the slides. Presenter notes provide a 45–60 second talk track per slide, architectural detail, and the boundaries between intended differentiation and proven capability. Earlier versions remain available below.

### Three-slide visual summary

- Status: condensed visual deck complete; rendered in PowerPoint with no text overflow
- Last refreshed: `2026-09-17 20:32:08`
- Scope: why the engine needs to be built; genetic algorithms, sources and custom models feeding execution graphs linked to LLM/neuro-symbolic reasoning; massive-context visualization and user customization

[Three-slide PowerPoint](../Artifacts/AMPHORA_Engine_VC_3_Slides_v2.pptx) · [PDF](../Artifacts/AMPHORA_Engine_VC_3_Slides_v2.pdf) · [Builder](build_vc_three_slides.py)

The diagrams and text are editable. Detailed competitive sources, prior-art context, and claim limits are retained in speaker notes. The full seven-slide deck below remains the expanded reference.

### Expanded reference

- Status: six core slides plus a linked competitive-source appendix complete
- Last refreshed: `2026-09-16 19:47:55`
- Audience: confidential venture-investor discussions
- Scope: unmet-need thesis, proposed differentiation, existing alternatives, why build, potential defensibility, and investment milestones
- Validation: seven slides rendered in PowerPoint; text overflow and shape bounds passed; PDF pages, notes, and 23 source hyperlinks checked
- Next gate: buyer/competitive diligence and measured pilot validation of the value hypotheses

[PowerPoint](../Artifacts/AMPHORA_Engine_VC_Positioning.pptx) · [PDF](../Artifacts/AMPHORA_Engine_VC_Positioning.pdf) · [Research and claim boundaries](VC_Positioning_Research.md) · [Builder](build_vc_engine_deck.py)

The competitive comparison uses official product descriptions, acknowledges overlapping capabilities, and presents Amphora's differentiation as a thesis to validate. It does not claim exclusive novelty, proven superiority, clinical readiness, customer traction, or measured returns. Current source-reviewed foundations are distinguished from the target engine. Rebuild with `py -3 docs/Presentations/build_vc_engine_deck.py`, then re-export the PDF from PowerPoint.
