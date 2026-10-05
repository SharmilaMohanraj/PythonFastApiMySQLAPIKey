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
- [x] STEP 11+: Earlier ASGITransport/FakeTicketService API report is invalidated and must be replaced by live HTTP evidence.
- [x] Remediation: `InternalNoteRepository.create_note` now updates its owning ticket's `updated_at` in the same transaction.
- [ ] Live verification: boot with Compose MySQL, execute real HTTP endpoint report, regenerate xlsx/docx, and complete Docker build/run verification with cleanup.
