# Checkpoint

## Design
- Mode: FastAPI greenfield, Python 3.10.16, FastAPI 0.110.0, direct `mysql-connector-python` persistence.
- Single cohesive Ticket/InternalNote domain group; reports are ticket repository queries, so it is implemented as one resource group to retain a single repository contract.
- Layers: Pydantic DTO schemas → thin routers with `Depends()` → `TicketService` → repositories → MySQL connection helpers.
- Service port: 8000. Compose infrastructure: `mysql:8.0.40`; app connects via `mysql` hostname in Compose.
- No authentication, messaging, seed data, or standalone testing framework. Pagination does not apply because no collection-list endpoint is requested.
- Error envelope: `{error: {code, message, timestamp, correlation_id}}`; request correlation middleware and centralized domain/validation/unhandled handlers.

## Progress
- [x] STEP 1: Entity/API design and endpoint classification (all eight declared API endpoints plus health/docs/OpenAPI are TESTABLE).
- [x] STEPS 2–7: Implemented layered ticket/note/report service and required infrastructure.
- [x] STEPS 9–10: README, dependency install, compile, import, and all eight route-table checks passed.
- [x] STEP 11+: Generated observed ASGI API report (13/13 PASS) and both report artifacts.
- [x] Boot attempts: issued 3/3; each failed at startup because `localhost:3306` refused MySQL connections. Docker daemon was unavailable, so image pull and final Docker build/run verification could not be attempted.
