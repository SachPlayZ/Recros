# Todo

## Plan

- [x] Add local authentication and protect user-scoped API routes.
- [x] Add production deployment artifacts and a reproducible container workflow.
- [x] Add scheduled retraining/health automation and operational documentation.
- [x] Validate authenticated browser/API flow and container build.
- [x] Add a runnable API with SQLite-backed catalog, profiles, events, and recommendations.
- [x] Add dataset seeding for the local movie, music, and book CSVs.
- [x] Add a browser UI for onboarding, recommendations, explanations, and feedback.
- [x] Connect the existing ML bundle as an optional ranking hook without making the app depend on it.

## Verification

- [x] Seed a clean local database from the bundled datasets.
- [x] Exercise health, profile, recommendations, and feedback API flows.
- [x] Run automated tests and a syntax/build check.

## Review

### Changed

- Added `apps/api` and `apps/web` end-to-end MVP.
- Added `run_recros.sh` and API setup documentation.

### Verified

- Seeded 360 local dataset items.
- Exercised health, user, profile, recommendation, catalog, and feedback endpoints.
- `unittest`, Python compile check, JavaScript syntax check, and browser HTML smoke check pass.
- Constrained ML run completed with `ml/config.mac_air.yaml`: 899,176 interactions, 350,000 training pairs, LightGBM best iteration 276, validation AUC 0.7535.
- Full ML run completed with `ml/config.full.yaml`: 19,982,331 interactions from 20,000,263 ratings, 650,000 training pairs, LightGBM best iteration 329, validation AUC 0.7606.
- Online API loaded the exported bundle and passed skip/like feedback-loop validation.
- Auth register/login/logout, bearer protection, guest tokens, and password hashing passed.
- Docker image built with OpenMP support; Compose container reached healthy status and passed the same API/feedback flow.

### Risks

- SQLite remains the default persistence layer; migrate to managed Postgres/pgvector when deploying beyond a single container.

### Follow-ups

- Add provider-specific managed Postgres/pgvector and external secret management if deploying publicly.
