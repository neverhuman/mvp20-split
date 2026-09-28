# Implementation Architecture

- Reference status: historical coatings-MVP implementation proposal. The current [Master Architecture](../../../Architecture.md) delegates v2 construction to its System Architecture child. The stack, endpoints and late-stage security/audit additions below are not the current v2 deployment or sequencing decisions; v2 requires authority and audit boundaries from its initial execution foundation.

## MVP Shape

The MVP is a web application for coatings formulation R&D:

```text
Browser SPA
  React + Vite
  Ingredients / Formulation Editor / Experiments / Suggestions
        |
        | HTTPS JSON, JWT bearer
        v
FastAPI API Gateway
  /api/v1/*
  auth, CORS, OpenAPI
        |
        +-- CRUD services
        +-- pure physics engine
        +-- pure suggestion engine
        |
        v
PostgreSQL
  SQLite allowed for tests
```

## Backend Principles

- Thin routers, fat services.
- Physics and ML modules are pure and stateless.
- Pure services do not import the database.
- Domain logic lives in services, not route handlers.
- API is versioned at `/api/v1`.
- Computed properties are recomputed from source records before being trusted.
- Formulation lineage is mandatory.

## Initial File Structure

```text
backend/
  app/
    main.py
    core/
      config.py
      db.py
      security.py
    models.py
    schemas.py
    api/
      deps.py
      auth.py
      ingredients.py
      formulations.py
      experiments.py
      suggestions.py
    services/
      physics.py
      optimizer.py
    seed.py
  tests/
    test_physics.py
    test_optimizer.py
    test_api.py

frontend/
  src/
    main.jsx
    App.jsx
    api.js
    styles.css
    pages/
      Login.jsx
      Ingredients.jsx
      Formulations.jsx
      FormulationEditor.jsx
      Experiments.jsx
      Suggest.jsx
```

## Initial Database Tables

- `users`
- `ingredients`
- `formulations`
- `formulation_components`
- `experiments`
- `measurements`

Near-term architecture should add:

- `programs`
- `product_envelopes`
- `candidate_campaigns`
- `candidates`
- `evidence_records`
- `candidate_packages`
- `source_records`
- `audit_events`

## API Surface

Initial `/api/v1` endpoints:

- `POST /auth/token`
- `GET /auth/me`
- `GET/POST /ingredients`
- `GET/PUT/DELETE /ingredients/{id}`
- `GET/POST /formulations`
- `GET/PUT/DELETE /formulations/{id}`
- `POST /formulations/{id}/clone`
- `GET /formulations/{id}/properties`
- `POST /formulations/preview-properties`
- `GET/POST /experiments`
- `GET/PUT/DELETE /experiments/{id}`
- `POST /experiments/{id}/measurements`
- `POST /suggestions`
- `GET /health`

Product-system endpoints to add after MVP:

- `GET/POST /programs`
- `GET/POST /product-envelopes`
- `POST /product-envelopes/{id}/sign-off`
- `POST /candidate-campaigns`
- `GET /candidates/{id}/evidence`
- `POST /evidence/intake`
- `POST /candidate-packages`
- `GET /audit/events`

## Physics Engine v1

All v1 physics are derived from formulation composition and ingredient constants:

- wet density: `1 / sum(w_i / rho_i)`
- solids by weight: `sum(w_i * solids_i)`
- solids by volume from per-ingredient solid volumes
- PVC from pigment/filler volume over pigment/filler plus binder-solids volume
- CPVC from pigment/filler oil absorption model
- VOC using EPA Method 24 convention
- binder Tg using Fox equation over binder solids
- cost per kg and per liter
- warnings for invalid compositions and envelope risk

## Suggestion Engine v1

Objective: given past composition-to-measurement pairs, propose the next batch.

- Fewer than 5 observations: space-filling Dirichlet sampling on constrained simplex.
- 5 or more observations: Gaussian Process with RBF kernel and Expected Improvement.
- Candidate generation respects per-ingredient min/max bounds and sum-to-1.0 composition.
- Returned candidates include predicted mean, uncertainty, and computed physics properties.

## Evolution Engine Direction

The `suggestions` endpoint should be treated as a bootstrap interface, not the final optimizer architecture. The preferred implementation style is an evolutionary campaign service:

```text
EvolutionCampaign
  -> GenerationRequest
  -> CandidateAttempt
  -> FitnessComponent
  -> SelectionDecision
```

Initial operation may use deterministic enumeration and hard-gate filtering. Later operation may enable genetic operators, Bayesian batch selection, or other active-learning strategies behind the same campaign contract.

Additional tables:

- `evolution_campaigns`
- `genomes`
- `generation_requests`
- `candidate_attempts`
- `fitness_components`
- `selection_decisions`
- `operator_registry`
- `generation_events`

Additional endpoints:

- `POST /evolution-campaigns`
- `GET /evolution-campaigns/{id}`
- `POST /evolution-campaigns/{id}/generate`
- `GET /evolution-campaigns/{id}/attempts`
- `GET /evolution-campaigns/{id}/fitness`
- `POST /evolution-campaigns/{id}/select`
- `GET /operators`

## Scaling Path

1. Move expensive physics/optimizer jobs behind a queue such as Celery or Arq with Redis.
2. Add Alembic migrations and read replicas when schema and load require them.
3. Add a model registry and model microservice boundary for property predictors.
4. Add multi-tenant `org_id` and row-level security when customer separation requires it.
5. Add lab instrument ingestion via CSV and later SiLA2-style integrations.
6. Add append-only audit event log for regulated customer requirements.
7. Add manufacturing release service for process windows, BOM, QC/SPC, and batch records.
