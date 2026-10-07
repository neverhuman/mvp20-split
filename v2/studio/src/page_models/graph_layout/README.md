# Bounded graph geometry

UI-01/G1. Owns local ELK layered placement and orthogonal edge routes for at most
200 visible nodes. Actual owner links and IDs are preserved; unknown endpoints
reject. Explicit208x72 node dimensions and fixed north/south ports permit measured
intersection checks. Input order is normalized for repeatability. No transport,
scientific inference, execution mutation or persisted state belongs here.

The canvas fences asynchronous geometry by its exact input key and clears obsolete
geometry on changes. Failure is visible; no misleading grid fallback. Status and
selection changes do not trigger relayout. Parent navigation owns scope and viewport.
Tests under tests/page_models/graph_layout cover geometric invariants and routing;
real browser acceptance separately verifies actual dimensions and readability.
