# Todo

## Plan

### Hybrid embedding upgrade

- [x] Add a provider-neutral embedding layer with a free local default (`BAAI/bge-small-en-v1.5`) and optional API provider configuration.
- [x] Build/version item embedding artifacts from title, description, creators, genres, tags, and domain metadata.
- [x] Add semantic candidate retrieval and user-profile embedding aggregation to the API recommender.
- [x] Fuse semantic, ratings/ranker, metadata, popularity, novelty, and diversity signals with safe fallbacks.
- [x] Wire the hybrid recommender into MCP tools and expose embedding/provider status in health output.
- [x] Add offline semantic/hybrid evaluation, regression tests, and demo documentation.
- [x] Run the constrained full loop, inspect recommendations, and record metrics/artifact locations.

### Decision

- Default: local open-source embeddings; no API key required.
- Optional: provider adapter can use a user-supplied API key later without changing MCP/API contracts.

### Unresolved questions

- None for the local demo path.

### MCP domain accuracy

- [x] Enforce requested recommendation domains in the core recommender.
- [x] Expose domain filters in MCP tools with all-domains default behavior.
- [x] Validate books-only, movies-only, books+movies, and default-all flows.

- [x] Add isolated Claude-compatible MCP server under `apps/mcp`.
- [x] Expose safe tools: catalog search, item details, one-favorite recommendations, and blended multi-favorite recommendations.
- [x] Reuse the existing catalog/recommender/model without changing API behavior.
- [x] Add title matching, domain disambiguation, bounded count, clear errors, and cleanup.
- [x] Add Claude Desktop stdio configuration and demo instructions.
- [x] Validate MCP protocol, tool behavior, cleanup, existing tests, and container health.
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
- MCP stdio protocol discovered all four tools and returned exactly five recommendations for `Interstellar`.
- MCP temporary profiles clean up without changing persistent user counts.
- Hybrid bundle completed with `BAAI/bge-small-en-v1.5`: 222,896 items × 384 dimensions; embedding artifact is local/free and API loads NumPy vectors only.
- Full constrained retrain completed: 19,982,331 interactions, 650,000 pairs, LightGBM best iteration 445, validation AUC 0.7608.
- Embedding sanity evaluation completed: 300 sampled items, cross-domain neighbor hit@5 0.0667.
- Local API health reported ranker and embeddings enabled; Interstellar MCP call returned five hybrid recommendations across movie/music domains.

### Risks

- SQLite remains the default persistence layer; migrate to managed Postgres/pgvector when deploying beyond a single container.
- The embedding build is CPU-heavy on the first run; it took about 33 minutes for the full 222,896-item catalog on this machine.

### Follow-ups

- Add provider-specific managed Postgres/pgvector and external secret management if deploying publicly.
- Optional: compare local BGE against a paid provider using the same versioned bundle/evaluation contract.
- MCP domain filtering completed and enforced server-side; omitted filter defaults to all three domains.
- Full MCP domain matrix passed: 3 single-domain cases, 3 two-domain combinations, and unrestricted all-domain behavior.
- Single-domain requests now return the full requested count instead of being capped by cross-domain diversity limits.
