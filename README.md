# Ticket Service

A FastAPI service for customer tickets and agent-only internal notes, backed by MySQL.

## Run with Docker Compose

```sh
docker compose up --build
```

The API is available at `http://localhost:8000`; health is at `/health` and generated OpenAPI documentation is at `/docs`.

## Endpoints

- `POST /tickets` — authenticated customer creates a ticket (`subject`, `description`, `priority`); ownership is derived from the API key.
- `GET /tickets/{ticket_id}` — get a ticket with creation-ordered internal notes
- `PATCH /tickets/{ticket_id}/assignment` — set `assigned_agent_id`
- `PATCH /tickets/{ticket_id}/status` — set one of `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`
- `POST /tickets/{ticket_id}/notes` — add an internal note
- `GET /reports/sla-breaches`
- `GET /reports/agent-resolution-times`
- `GET /reports/open-ticket-counts-by-priority`
- `POST /tickets/{ticket_id}/feedback` — an authenticated `customer` may submit exactly one satisfaction rating for their own `CLOSED` ticket. The JSON body requires an integer `rating` from 1 through 5 and accepts an optional `comment`.
- `GET /agents/{agent_id}/satisfaction` — authenticated `agent` and `supervisor` callers can retrieve the requested agent's average rating from feedback on `RESOLVED` or `CLOSED` tickets. The average is `null` when no qualifying feedback exists.
- `GET /supervisor/low-rated-tickets` — authenticated `supervisor` callers can review feedback rated 1 or 2, including the ticket ID, rating, and optional comment.
- `GET /supervisor/pending-feedback` — authenticated `supervisor` callers can review `CLOSED` tickets that have no feedback row; each item exposes `pending_feedback: true`.

Ticket creation and feedback routes use the `X-API-Key` header. API keys are opaque credentials resolved against the server-side `AUTH_API_KEYS` JSON map; clients cannot set an identity or role through headers, and `customer_id` is not accepted in ticket requests. Each map value supplies an `id` and one allowed role (`customer`, `agent`, or `supervisor`). Local Compose provides `local-customer-key`, `local-agent-key`, and `local-supervisor-key` only for development; replace them with secret-managed credentials in deployment. The supervisor review endpoints use offset pagination: `offset` defaults to 0 and `limit` defaults to 20; offsets cannot be negative and limits must be positive. Their response includes `items`, `total`, `limit`, and `offset`.

Priorities are `LOW`, `MEDIUM`, `HIGH`, and `URGENT`. `URGENT` tickets breach after two hours and `HIGH` tickets breach after eight hours when unresolved or resolved too late.

Configuration uses `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`, and required `AUTH_API_KEYS`; see `.env.example`. Errors have a consistent envelope with a correlation ID, which can be supplied using `X-Correlation-ID`.
