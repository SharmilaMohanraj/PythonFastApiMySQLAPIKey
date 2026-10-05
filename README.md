# Ticket Service

A FastAPI service for customer tickets and agent-only internal notes, backed by MySQL.

## Run with Docker Compose

```sh
docker compose up --build
```

The API is available at `http://localhost:8000`; health is at `/health` and generated OpenAPI documentation is at `/docs`.

## Endpoints

- `POST /tickets` — create a ticket (`subject`, `description`, `priority`)
- `GET /tickets/{ticket_id}` — get a ticket with creation-ordered internal notes
- `PATCH /tickets/{ticket_id}/assignment` — set `assigned_agent_id`
- `PATCH /tickets/{ticket_id}/status` — set one of `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`
- `POST /tickets/{ticket_id}/notes` — add an internal note
- `GET /reports/sla-breaches`
- `GET /reports/agent-resolution-times`
- `GET /reports/open-ticket-counts-by-priority`

Priorities are `LOW`, `MEDIUM`, `HIGH`, and `URGENT`. `URGENT` tickets breach after two hours and `HIGH` tickets breach after eight hours when unresolved or resolved too late.

Configuration uses `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE`; see `.env.example`. Errors have a consistent envelope with a correlation ID, which can be supplied using `X-Correlation-ID`.
