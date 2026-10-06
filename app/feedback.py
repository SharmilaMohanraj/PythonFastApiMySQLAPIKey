"""Feedback API router and idempotent feedback storage initialization."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.auth import AuthenticatedPrincipal, require_roles
from app.db import connection
from app.dependencies import get_feedback_service
from app.feedback_service import FeedbackService
from app.schemas import (
    AgentSatisfactionResponse,
    FeedbackCreate,
    FeedbackResponse,
    LowRatedTicketPage,
    PendingFeedbackTicketPage,
)

feedback_router = APIRouter(tags=["feedback"])
FeedbackServiceDependency = Annotated[FeedbackService, Depends(get_feedback_service)]
CustomerPrincipal = Annotated[AuthenticatedPrincipal, Depends(require_roles("customer"))]
AgentOrSupervisorPrincipal = Annotated[AuthenticatedPrincipal, Depends(require_roles("agent", "supervisor"))]
SupervisorPrincipal = Annotated[AuthenticatedPrincipal, Depends(require_roles("supervisor"))]
Offset = Annotated[int, Query(ge=0, description="Number of matching items to skip")]
Limit = Annotated[int, Query(gt=0, description="Maximum number of matching items to return")]


def initialize_feedback_storage() -> None:
    """Create feedback storage and ticket ownership support; safe on every startup."""
    feedback_table_sql = """CREATE TABLE IF NOT EXISTS feedback (
        id INT AUTO_INCREMENT PRIMARY KEY,
        ticket_id INT NOT NULL,
        rating TINYINT NOT NULL,
        comment TEXT NULL,
        created_at DATETIME NOT NULL,
        CONSTRAINT chk_feedback_rating CHECK (rating BETWEEN 1 AND 5),
        CONSTRAINT uq_feedback_ticket UNIQUE (ticket_id),
        CONSTRAINT fk_feedback_ticket FOREIGN KEY (ticket_id)
            REFERENCES tickets(id) ON DELETE CASCADE
    ) ENGINE=InnoDB"""
    with connection() as database_connection:
        cursor = database_connection.cursor()
        try:
            # MySQL 8.0 does not consistently support ADD COLUMN IF NOT EXISTS.
            # Check metadata first so startup remains idempotent across supported images.
            cursor.execute("SHOW COLUMNS FROM tickets LIKE 'customer_id'")
            if cursor.fetchone() is None:
                cursor.execute("ALTER TABLE tickets ADD COLUMN customer_id VARCHAR(255) NULL")
            cursor.execute(feedback_table_sql)
        finally:
            cursor.close()


@feedback_router.post(
    "/tickets/{ticket_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_feedback(
    ticket_id: int,
    payload: FeedbackCreate,
    principal: CustomerPrincipal,
    service: FeedbackServiceDependency,
) -> dict:
    return service.submit(ticket_id, payload, principal)


@feedback_router.get("/agents/{agent_id}/satisfaction", response_model=AgentSatisfactionResponse)
def agent_satisfaction(
    agent_id: str,
    _: AgentOrSupervisorPrincipal,
    service: FeedbackServiceDependency,
) -> dict:
    return service.agent_satisfaction(agent_id)


@feedback_router.get("/supervisor/low-rated-tickets", response_model=LowRatedTicketPage)
def low_rated_tickets(
    _: SupervisorPrincipal,
    service: FeedbackServiceDependency,
    offset: Offset = 0,
    limit: Limit = 20,
) -> dict:
    return service.low_rated_tickets(offset, limit)


@feedback_router.get("/supervisor/pending-feedback", response_model=PendingFeedbackTicketPage)
def pending_feedback(
    _: SupervisorPrincipal,
    service: FeedbackServiceDependency,
    offset: Offset = 0,
    limit: Limit = 20,
) -> dict:
    return service.pending_feedback_tickets(offset, limit)
